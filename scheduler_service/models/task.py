from datetime import datetime
from typing import List
from tortoise.models import Model
from tortoise import fields, Tortoise

# 定义有效的HTTP方法列表
VALID_HTTP_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']


class RequestTask(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=32)
    interval = fields.IntField(null=True)  # 存储间隔多少秒
    random_interval_seconds_min = fields.IntField(null=True)  # 最小浮动时间
    random_interval_seconds_max = fields.IntField(null=True)  # 最大浮动时间
    start_time = fields.DatetimeField(auto_now_add=True)
    request_url = fields.CharField(max_length=128)
    callback_url = fields.CharField(max_length=128)
    callback_token = fields.CharField(max_length=64, null=True)  # 用于callback_url登录的token
    header = fields.JSONField(null=True)  # HTTP请求头字段
    method = fields.CharField(max_length=10, default='GET')  # HTTP请求方法
    body = fields.JSONField(default=dict) 

    # 定义与User的外键关系
    user = fields.ForeignKeyField('models.User', related_name='request_tasks', source_field='user_id')

    async def save(self, *args, **kwargs):
        # 验证method是否是有效的HTTP方法
        if self.method and self.method.upper() not in VALID_HTTP_METHODS:
            raise ValueError(f"Invalid HTTP method: {self.method}. Must be one of {VALID_HTTP_METHODS}")
        # 保存前转换为大写
        self.method = self.method.upper()
        await super().save(*args, **kwargs)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "interval": self.interval,
            "random_interval_seconds_min": self.random_interval_seconds_min,
            "random_interval_seconds_max": self.random_interval_seconds_max,
            "start_time": self.start_time,
            "user_id": self.user.id if self.user else None,
            "request_url": self.request_url,
            "callback_url": self.callback_url,
            "callback_token": self.callback_token,
            "header": self.header,
            "method": self.method,
            "body": self.body
        }