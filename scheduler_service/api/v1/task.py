import time
from datetime import datetime
from typing import List

from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.base import JobLookupError
from fastapi import APIRouter, Depends, HTTPException, status
from dramatiq_abort import abort

from scheduler_service import get_scheduler, logger
from scheduler_service.api.decorators import login_require
from scheduler_service.api.schemas import RequestTaskCreate
from scheduler_service.models import RequestTask, User
from scheduler_service.service.request import ping, trigger_cron_task


async def _create_single_task(task_data: RequestTaskCreate, user_id: int) -> RequestTask:
    """Internal helper to create a single task"""
    # Determine start_time: use provided or default to now (timestamp in seconds)
    if task_data.start_time:
        start_ts = int(task_data.start_time)
    else:
        start_ts = int(time.time())

    # Create request task
    task = await RequestTask.create(
        name=task_data.name,
        user_id=user_id,
        start_time=start_ts,
        request_url=task_data.request_url,
        callback_url=task_data.callback_url,
        callback_token=task_data.callback_token,
        header=task_data.header,
        method=task_data.method,
        body=task_data.body if task_data.body is not None else {},
        cron=task_data.cron
    )

    # If cron is set, add to scheduler
    if task.cron:
        try:
            scheduler = get_scheduler()
            # Validate and create cron trigger
            trigger = CronTrigger.from_crontab(task.cron)
            job = scheduler.add_job(
                trigger_cron_task,
                trigger,
                args=[task.id],
                misfire_grace_time=60,
                coalesce=True
            )
            task.job_id = job.id
        except ValueError as e:
            # If cron expression is invalid, delete created task and raise exception
            await task.delete()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid cron expression: {str(e)}"
            )
    else:
        # If cron is not set, check if start_time is in the future
        # If task_data.start_time is None, it means immediate execution, eta_ms set to 0 or current time
        if task_data.start_time:
            eta_ms = int(task_data.start_time * 1000)
            current_ms = int(time.time() * 1000)

            if eta_ms > current_ms:
                # If it is future time, use eta to delay sending
                message = ping.send_with_options(args=[task.id], eta=eta_ms)
            else:
                # Otherwise send immediately
                message = ping.send(task.id)
        else:
            # No start_time, send immediately
            message = ping.send(task.id)

        task.message_id = message.message_id

    await task.save()
    return task


async def get_tasks(current_user: User = Depends(login_require)):
    """Get all request tasks for current user"""
    tasks = await RequestTask.filter(user_id=current_user.id)
    return {
        "tasks": [t.to_dict() for t in tasks]
    }


async def create_task(task_data: RequestTaskCreate, current_user: User = Depends(login_require)):
    """Create new request task"""
    task = await _create_single_task(task_data, current_user.id)
    return {
        'task_id': task.id
    }


async def bulk_create_task(tasks_data: List[RequestTaskCreate], current_user: User = Depends(login_require)):
    """Bulk create request tasks"""
    task_ids = []
    # Simple loop creation. If higher performance is needed, consider Tortoise's bulk_create,
    # but since each task needs separate scheduling and message queue handling, simple loop is easier to maintain and logically correct.
    for task_data in tasks_data:
        task = await _create_single_task(task_data, current_user.id)
        task_ids.append(task.id)

    return {
        'task_ids': task_ids
    }


async def get_task(task_id: int, current_user: User = Depends(login_require)):
    """Get specified request task info"""
    # Validate if task belongs to current user
    task = await RequestTask.get_or_none(id=task_id, user_id=current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request task not found"
        )

    return task.to_dict()


async def delete_task(task_id: int, current_user: User = Depends(login_require)):
    """Delete request task (also attempt to cancel queued messages and scheduled tasks)"""
    # Validate if task belongs to current user
    task = await RequestTask.get_or_none(id=task_id, user_id=current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request task not found"
        )

    # Attempt to cancel queued one-time task
    if task.message_id:
        try:
            abort(task.message_id)
        except Exception:
            # Ignore abort failure
            pass

    # Attempt to remove recurring task from scheduler
    if task.job_id:
        try:
            scheduler = get_scheduler()
            scheduler.remove_job(task.job_id)
        except JobLookupError:
            # Ignore task not found error (likely finished or already removed)
            logger.info(
                "Cron task %s not found in scheduler (likely finished or already removed).", task.job_id)
            pass
        except Exception as e:
            # Ignore other scheduler errors, do not affect database record deletion
            logger.error(
                "Error removing cron task %s from scheduler: %s", task.job_id, e)
            pass

    await task.delete()
    return None

router = APIRouter()

router.add_api_route("", get_tasks, methods=["GET"])
router.add_api_route("", create_task, methods=["POST"])
router.add_api_route("/bulk", bulk_create_task, methods=["POST"])
router.add_api_route("/{task_id}", get_task, methods=["GET"])
router.add_api_route("/{task_id}", delete_task, methods=["DELETE"])
