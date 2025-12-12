"""API module initialization"""
from fastapi import APIRouter

from scheduler_service.api.v1 import task, user, stats, apikey


def setup_routes(app):
    """Setup routes"""
    # Create API router
    api_router = APIRouter()

    # Register v1 routes
    api_router.include_router(task.router, prefix="/tasks", tags=["tasks"])
    api_router.include_router(user.router, prefix="/users", tags=["users"])
    api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
    api_router.include_router(
        apikey.router, prefix="/apikeys", tags=["apikeys"])

    # Register API router to app
    app.include_router(api_router, prefix="/api/v1")
