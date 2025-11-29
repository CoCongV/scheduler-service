from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, field_validator

# Define valid HTTP methods
VALID_HTTP_METHODS = ['GET', 'POST', 'PUT',
                      'DELETE', 'PATCH', 'HEAD', 'OPTIONS']


class RequestTaskCreate(BaseModel):
    """Request task creation model"""
    name: str
    start_time: Optional[float] = None
    header: Optional[dict] = None  # HTTP request header fields
    method: Optional[Literal['GET', 'POST', 'PUT', 'DELETE',
                             'PATCH', 'HEAD', 'OPTIONS']] = 'GET'  # HTTP request method
    request_url: str
    callback_url: Optional[str] = None
    callback_token: Optional[str] = None  # Token for callback_url login
    body: Optional[dict] = None  # HTTP request body
    cron: Optional[str] = None  # cron expression

    @field_validator('method')
    @classmethod
    def validate_method(cls, v):
        if v and v.upper() not in VALID_HTTP_METHODS:
            raise ValueError(
                f"Invalid HTTP method: {v}. Must be one of {VALID_HTTP_METHODS}")
        return v.upper()


class RequestTaskResponse(BaseModel):
    """Request task response model"""
    id: int
    name: str
    user_id: int
    start_time: Optional[int]
    request_url: str
    callback_url: Optional[str]
    callback_token: Optional[str] = None  # Token for callback_url login
    header: Optional[dict] = None  # HTTP request header fields
    method: str = 'GET'  # HTTP request method
    body: Optional[dict] = None  # HTTP request body
    cron: Optional[str] = None  # cron expression
    cron_count: int = 0  # Number of times cron task has looped
    job_id: Optional[str] = None  # APScheduler Job ID
    status: str = "PENDING"
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DashboardStats(BaseModel):
    """Dashboard statistics model"""
    total_tasks: int
    status_counts: dict[str, int]
