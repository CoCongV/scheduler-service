import dramatiq
import httpx
from tortoise.expressions import F

from scheduler_service.constants import RequestStatus, TaskStatus
from scheduler_service.models import RequestTask
from scheduler_service.utils.logger import logger

# Define global session
_session = None


def get_session():
    """Get httpx session"""
    global _session
    if _session is None or _session.is_closed:
        _session = httpx.AsyncClient(timeout=60.0)
    return _session


async def close_session():
    """Close httpx session"""
    global _session
    if _session and not _session.is_closed:
        await _session.aclose()


async def trigger_cron_task(task_id):
    """
    Task trigger called by APScheduler.
    Send task to Dramatiq and update loop count.
    """
    # Send task to message queue
    try:
        ping.send(task_id)
    except Exception as e:
        logger.error("Failed to send task %s to Dramatiq: %s", task_id, e)

    # Update loop count
    # Use F expression for atomic update
    try:
        await RequestTask.filter(id=task_id).update(cron_count=F('cron_count') + 1)
    except Exception as e:
        logger.error("Failed to update cron count for task %s: %s", task_id, e)


@dramatiq.actor
async def ping(task_id):
    """Execute ping task"""
    session = get_session()
    callback_data = None

    # Get task info from database
    task = await RequestTask.get_or_none(id=task_id)
    if not task:
        logger.warning("Task with id %s not found", task_id)
        return

    # Update status to running, and clear previous error message
    task.status = TaskStatus.RUNNING
    task.error_message = None
    await task.save()

    try:
        # Prepare request parameters
        url = task.request_url
        kwargs = {
            'headers': task.header if task.header else {}
        }

        # If body exists, use it as request body
        if task.body:
            kwargs['json'] = task.body

        # Execute HTTP request
        response = await session.request(task.method, url, **kwargs)

        # Read response content
        content = await response.aread()
        callback_data = {
            'response': content.decode('utf-8'),
            'code': response.status_code,
            'exception': None,
            'status': RequestStatus.COMPLETE
        }

        # Update status to completed
        task.status = TaskStatus.COMPLETED
        await task.save()

    except Exception as e:
        # Handle request exception
        logger.error("Error requesting task %s: %s", task_id, e)
        callback_data = {
            'response': None,
            'code': None,
            'exception': str(e),
            'status': RequestStatus.FAIL
        }
        # Update status to failed, and record error message
        task.status = TaskStatus.FAILED
        task.error_message = str(e)
        await task.save()

    # Send callback (regardless of success or failure, as long as there is a callback URL and callback data)
    if task.callback_url and callback_data:
        try:
            await session.post(
                task.callback_url,
                json=callback_data
            )
        except Exception as e:
            logger.error("Error sending callback to %s: %s",
                         task.callback_url, e)


# Register startup and shutdown hooks
@dramatiq.actor
async def startup_worker():
    """Execute when worker starts"""
    global _session
    _session = httpx.AsyncClient(timeout=60.0)


@dramatiq.actor
async def shutdown_worker():
    """Execute when worker shuts down"""
    await close_session()
