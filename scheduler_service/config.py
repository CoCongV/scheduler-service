import json
import logging
from datetime import datetime


class CustomJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class Config:
    NAME = "scheduler_service"
    PG_URL = "postgresql://postgres:postgres@localhost:5432/scheduler"
    SECRET_KEY = 'your_secret_key'
    RESTFUL_JSON = {"cls": CustomJsonEncoder}
    LOG_LEVEL = logging.DEBUG

    DRAMATIQ_URL = "amqp://guest:guest@localhost:25672/%2F"

    @classmethod
    def to_dict(cls):
        return {k: v for k, v in cls.__dict__.items() if not k.startswith('__')}
