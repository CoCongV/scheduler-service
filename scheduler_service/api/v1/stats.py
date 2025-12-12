from fastapi import APIRouter, Depends
from tortoise.functions import Count

from scheduler_service.api.decorators import login_require
from scheduler_service.api.schemas import DashboardStats
from scheduler_service.constants import TaskStatus
from scheduler_service.models import RequestTask, User


async def get_dashboard_stats(current_user: User = Depends(login_require)) -> DashboardStats:
    """Get dashboard statistics"""
    # Get total task count
    total_tasks = await RequestTask.filter(user_id=current_user.id).count()

    # Get task count by status
    # Use simple query loop since status count is small and fixed
    status_counts = {}
    for status in [TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
        count = await RequestTask.filter(user_id=current_user.id, status=status).count()
        if count > 0:
            status_counts[status] = count

    return DashboardStats(
        total_tasks=total_tasks,
        status_counts=status_counts
    )


router = APIRouter()
router.add_api_route("/dashboard", get_dashboard_stats,
                     methods=["GET"], response_model=DashboardStats)
