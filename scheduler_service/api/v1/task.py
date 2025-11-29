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

    # 创建请求任务
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

    # 如果设置了cron，添加到调度器
    if task.cron:
        try:
            scheduler = get_scheduler()
            # 验证并创建cron触发器
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
            # 如果cron表达式无效，删除已创建的任务并抛出异常
            await task.delete()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid cron expression: {str(e)}"
            )
    else:
        # 如果没有设置cron，则检查 start_time 是否在未来
        # 如果 task_data.start_time 为 None，说明是立即执行，eta_ms 设为 0 或当前时间
        if task_data.start_time:
            eta_ms = int(task_data.start_time * 1000)
            current_ms = int(time.time() * 1000)

            if eta_ms > current_ms:
                # 如果是未来时间，使用 eta 延迟发送
                message = ping.send_with_options(args=[task.id], eta=eta_ms)
            else:
                # 否则立即发送
                message = ping.send(task.id)
        else:
            # 没有 start_time，立即发送
            message = ping.send(task.id)

        task.message_id = message.message_id

    await task.save()
    return task


async def get_tasks(current_user: User = Depends(login_require)):
    """获取当前用户的所有请求任务"""
    tasks = await RequestTask.filter(user_id=current_user.id)
    return {
        "tasks": [t.to_dict() for t in tasks]
    }


async def create_task(task_data: RequestTaskCreate, current_user: User = Depends(login_require)):
    """创建新请求任务"""
    task = await _create_single_task(task_data, current_user.id)
    return {
        'task_id': task.id
    }


async def bulk_create_task(tasks_data: List[RequestTaskCreate], current_user: User = Depends(login_require)):
    """批量创建请求任务"""
    task_ids = []
    # 简单的循环创建。如果需要更高的性能，可以考虑 Tortoise 的 bulk_create，
    # 但因为每个任务都需要单独处理调度和消息队列，简单的循环更容易维护且逻辑正确。
    for task_data in tasks_data:
        task = await _create_single_task(task_data, current_user.id)
        task_ids.append(task.id)

    return {
        'task_ids': task_ids
    }


async def get_task(task_id: int, current_user: User = Depends(login_require)):
    """获取指定请求任务信息"""
    # 验证任务是否属于当前用户
    task = await RequestTask.get_or_none(id=task_id, user_id=current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="请求任务不存在"
        )

    return task.to_dict()


async def delete_task(task_id: int, current_user: User = Depends(login_require)):
    """删除请求任务（同时尝试取消排队中的消息和定时任务）"""
    # 验证任务是否属于当前用户
    task = await RequestTask.get_or_none(id=task_id, user_id=current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="请求任务不存在"
        )

    # 尝试取消排队中的一次性任务
    if task.message_id:
        try:
            abort(task.message_id)
        except Exception:
            # 忽略中止失败
            pass

    # 尝试从调度器移除循环任务
    if task.job_id:
        try:
            scheduler = get_scheduler()
            scheduler.remove_job(task.job_id)
        except JobLookupError:
            # 忽略任务未找到错误（可能已经执行完或被手动移除了）
            logger.info(
                "Cron task %s not found in scheduler (likely finished or already removed).", task.job_id)
            pass
        except Exception as e:
            # 忽略其他调度器错误，不影响删除数据库记录
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
