from datetime import datetime
import json


class CustomJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class Config:
    NAME = "scheduler_service"
    PG_URL = "postgresql://localhost/scheduler"
    SECRET_KEY = 'your_secret_key'
    RESTFUL_JSON = {"cls": CustomJsonEncoder}
    
    # RabbitMQ配置默认值
    RABBITMQ_USER = "guest"
    RABBITMQ_PASSWORD = "guest"
    RABBITMQ_HOST = "localhost"
    RABBITMQ_PORT = 5672
    RABBITMQ_VHOST = "%2F"

    @classmethod
    def to_dict(cls):
        return {k: v for k, v in cls.__dict__.items() if not k.startswith('__')}