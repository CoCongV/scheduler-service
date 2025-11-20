from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TaskCreate(BaseModel):
    """任务创建模型"""
    name: str
    interval: Optional[int] = None
    start_time: int
    header: Optional[dict] = None  # 从cookies更新为header
    request_url: str
    callback_url: Optional[str] = None


class URLDetailCreate(BaseModel):
    """URL详情创建模型"""
    name: Optional[str] = None
    payload: Optional[dict] = None  # 从params更新为payload
    header: Optional[dict] = None  # 添加header字段


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