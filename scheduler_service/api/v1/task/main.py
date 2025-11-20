from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from fastapi import HTTPException, status, Depends
from scheduler_service.api.decorators import login_require
from scheduler_service.models import User, Task, URLDetail
from scheduler_service.config import Config


class TaskCreate(BaseModel):
    """任务创建模型"""
    name: str
    interval: Optional[int] = None
    start_time: int
    cookies: Optional[str] = None
    request_url: str
    callback_url: Optional[str] = None


class URLDetailCreate(BaseModel):
    """URL详情创建模型"""
    name: Optional[str] = None
    params: Optional[dict] = None


class TaskResponse(BaseModel):
    """任务响应模型"""
    id: int
    name: str
    interval: Optional[int]
    user_id: int
    start_time: datetime
    request_url: str
    callback_url: Optional[str]
    
    class Config:
        orm_mode = True


async def get_tasks(current_user: User = Depends(login_require)):
    """获取当前用户的所有任务"""
    tasks = await Task.filter(user_id=current_user.id)
    return {
        "tasks": [t.to_dict() for t in tasks]
    }


async def create_task(task_data: TaskCreate, current_user: User = Depends(login_require)):
    """创建新任务"""
    # 移除任务数量限制检查

    # 创建任务
    task = await Task.create(
        name=task_data.name,
        interval=task_data.interval,
        user_id=current_user.id,
        start_time=datetime.fromtimestamp(task_data.start_time),
        request_url=task_data.request_url,
        callback_url=task_data.callback_url
    )
    return {
        'task_id': task.id
    }


async def get_task(task_id: int, current_user: User = Depends(login_require)):
    """获取指定任务信息"""
    # 验证任务是否属于当前用户
    task = await Task.get_or_none(id=task_id, user_id=current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    return task.to_dict()


async def create_url_detail(
    task_id: int,
    url_data: URLDetailCreate,
    current_user: User = Depends(login_require)
):
    """为任务添加URL详情"""
    # 验证任务是否属于当前用户
    task = await Task.get_or_none(id=task_id, user_id=current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 移除URL数量限制检查
    
    # 创建URL详情
    url_detail = await URLDetail.create(
        name=url_data.name,
        params=url_data.params,
        task_id=task_id
    )
    return {
        'url_id': url_detail.id
    }


async def delete_task(task_id: int, current_user: User = Depends(login_require)):
    """删除任务"""
    # 验证任务是否属于当前用户
    task = await Task.get_or_none(id=task_id, user_id=current_user.id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 删除任务及其关联的URL详情
    await URLDetail.filter(task_id=task_id).delete()
    await task.delete()
    return None