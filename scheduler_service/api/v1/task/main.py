from datetime import datetime
from fastapi import HTTPException, status, Depends
from scheduler_service.api.decorators import login_require
from scheduler_service.models import User, RequestTask, URLDetail
from scheduler_service.config import Config
from scheduler_service.api.schemas import RequestTaskCreate, URLDetailCreate


async def get_tasks(current_user: User = Depends(login_require)):
    """获取当前用户的所有请求任务"""
    tasks = await RequestTask.filter(user_id=current_user.id)
    return {
        "tasks": [t.to_dict() for t in tasks]
    }


async def create_task(task_data: RequestTaskCreate, current_user: User = Depends(login_require)):
    """创建新请求任务"""
    # 创建请求任务
    task = await RequestTask.create(
        name=task_data.name,
        interval=task_data.interval,
        user_id=current_user.id,
        start_time=datetime.fromtimestamp(task_data.start_time),
        request_url=task_data.request_url,
        callback_url=task_data.callback_url,
        callback_token=task_data.callback_token,  # 从请求中读取callback_token
        header=task_data.header,
        method=task_data.method
    )
    return {
        'task_id': task.id
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


async def create_url_detail(
    task_id: int,
    url_data: URLDetailCreate,
    current_user: User = Depends(login_require)
):
    """为请求任务添加URL详情"""
    # 验证任务是否属于当前用户
    task = await RequestTask.get_or_none(id=task_id, user_id=current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="请求任务不存在"
        )

    # 移除URL数量限制检查

    # 创建URL详情
    url_detail = await URLDetail.create(
        name=url_data.name,
        payload=url_data.payload,
        request_task_id=task_id
    )
    return {
        'url_id': url_detail.id
    }


async def delete_task(task_id: int, current_user: User = Depends(login_require)):
    """删除请求任务"""
    # 验证任务是否属于当前用户
    task = await RequestTask.get_or_none(id=task_id, user_id=current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="请求任务不存在"
        )

    # 删除任务及其关联的URL详情
    await URLDetail.filter(request_task_id=task_id).delete()
    await task.delete()
    return None