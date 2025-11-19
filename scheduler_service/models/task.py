from datetime import datetime

from tortoise.models import Model
from tortoise import fields


class Task(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=32)
    interval = fields.IntField(null=True)  # 存储间隔多少秒
    random_interval_seconds_min = fields.IntField(null=True)  # 最小浮动时间
    random_interval_seconds_max = fields.IntField(null=True)  # 最大浮动时间
    start_time = fields.DatetimeField(auto_now_add=True)

    # 定义与User的外键关系
    user = fields.ForeignKeyField('models.User', related_name='tasks', source_field='user_id')

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "interval": self.interval,
            "random_interval_seconds_min": self.random_interval_seconds_min,
            "random_interval_seconds_max": self.random_interval_seconds_max,
            "start_time": self.start_time,
            "user_id": self.user.id
        }


class URLDetail(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=32)
    request_url = fields.CharField(max_length=128)
    callback_url = fields.CharField(max_length=128)
    params = fields.JSONField(default=dict)
    cookies = fields.JSONField(null=True)  # 从Task模型迁移过来的cookies字段

    # 定义与Task的外键关系
    task = fields.ForeignKeyField('models.Task', related_name='url_details', source_field='task_id')
