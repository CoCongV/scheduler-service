"""任务API路由模块"""
from fastapi import APIRouter
from .main import (
    get_tasks,
    create_task,
    get_task,
    create_url_detail,
    delete_task
)


router = APIRouter(prefix="/tasks", tags=["tasks"])

# 注册任务相关路由
router.get("", response_model=dict)(get_tasks)
router.post("", status_code=201)(create_task)
router.get("/{task_id}")(get_task)
router.post("/{task_id}/urls", status_code=201)(create_url_detail)
router.delete("/{task_id}", status_code=204)(delete_task)