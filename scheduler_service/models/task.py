from tortoise import fields
from tortoise.models import Model

from scheduler_service.constants import TaskStatus

# Define valid HTTP methods list
VALID_HTTP_METHODS = ['GET', 'POST', 'PUT',
                      'DELETE', 'PATCH', 'HEAD', 'OPTIONS']


class RequestTask(Model):
    """Request task model"""
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=32)
    start_time = fields.BigIntField(null=True)  # Unix timestamp in seconds
    request_url = fields.CharField(max_length=128)
    callback_url = fields.CharField(max_length=128, null=True)
    callback_token = fields.CharField(
        max_length=64, null=True)  # Token for callback_url login
    header = fields.JSONField(null=True)  # HTTP request header fields
    method = fields.CharField(
        max_length=10, default='GET')  # HTTP request method
    body = fields.JSONField(default=dict)
    message_id = fields.CharField(
        max_length=64, null=True)  # Dramatiq message ID
    cron = fields.CharField(max_length=64, null=True)  # cron expression
    # Number of times cron task has looped
    cron_count = fields.IntField(default=0)
    job_id = fields.CharField(max_length=64, null=True)  # APScheduler Job ID
    status = fields.CharField(max_length=20, default=TaskStatus.PENDING)
    # Error message when task execution fails
    error_message = fields.TextField(null=True)

    # Define foreign key relationship with User
    user = fields.ForeignKeyField(
        'models.User', related_name='request_tasks', source_field='user_id')
    user_id: int

    async def save(self, *args, **kwargs):
        # Validate if method is a valid HTTP method
        if self.method and self.method.upper() not in VALID_HTTP_METHODS:
            raise ValueError(
                f"Invalid HTTP method: {self.method}. Must be one of {VALID_HTTP_METHODS}")

        # Validate if request_url contains protocol
        if self.request_url and not self.request_url.startswith(('http://', 'https://')):
            raise ValueError(
                f"Invalid request URL: {self.request_url}. Must start with 'http://' or 'https://'")

        # Validate if callback_url contains protocol
        if self.callback_url and not self.callback_url.startswith(('http://', 'https://')):
            raise ValueError(
                f"Invalid callback URL: {self.callback_url}. Must start with 'http://' or 'https://'")

        # Convert to uppercase before saving
        self.method = self.method.upper()
        await super().save(*args, **kwargs)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "start_time": self.start_time,
            "user_id": self.user_id,
            "request_url": self.request_url,
            "callback_url": self.callback_url,
            "callback_token": self.callback_token,
            "header": self.header,
            "method": self.method,
            "body": self.body,
            "message_id": self.message_id,
            "cron": self.cron,
            "cron_count": self.cron_count,
            "job_id": self.job_id,
            "status": self.status,
            "error_message": self.error_message
        }
