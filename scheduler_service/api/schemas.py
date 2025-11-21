from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, validator

# 定义有效的HTTP方法
VALID_HTTP_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']


class RequestTaskCreate(BaseModel):
    """请求任务创建模型"""
    name: str
    interval: Optional[int] = None
    start_time: int
    header: Optional[dict] = None  # HTTP请求头字段
    method: Optional[Literal['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']] = 'GET'  # HTTP请求方法
    request_url: str
    callback_url: Optional[str] = None
    callback_token: Optional[str] = None  # 用于callback_url登录的token

    @validator('method')
    def validate_method(cls, v):
        if v and v.upper() not in VALID_HTTP_METHODS:
            raise ValueError(f"Invalid HTTP method: {v}. Must be one of {VALID_HTTP_METHODS}")
        return v.upper()


class URLDetailCreate(BaseModel):
    """URL详情创建模型"""
    name: Optional[str] = None
    payload: Optional[dict] = None  # 从params更新为payload


class RequestTaskResponse(BaseModel):
    """请求任务响应模型"""
    id: int
    name: str
    interval: Optional[int]
    user_id: int
    start_time: datetime
    request_url: str
    callback_url: Optional[str]
    callback_token: Optional[str] = None  # 用于callback_url登录的token
    header: Optional[dict] = None  # HTTP请求头字段
    method: str = 'GET'  # HTTP请求方法

    class Config:
        orm_mode = True