import json
import logging
import os
from datetime import datetime


class CustomJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class Config:
    NAME = "scheduler_service"
    PG_URL = os.getenv(
        "PG_URL", "postgres://postgres:postgres@localhost:5432/scheduler"
    )
    SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
    RESTFUL_JSON = {"cls": CustomJsonEncoder}
    LOG_LEVEL = logging.DEBUG
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Default Admin User Configuration
    DEFAULT_ADMIN_NAME = os.getenv("DEFAULT_ADMIN_NAME", "admin")
    DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@admin.com")
    DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin")

    @classmethod
    def load(cls):
        """Deprecated: Config is now loaded from environment variables."""
        return cls

    @classmethod
    def to_dict(cls):
        return {
            k: v
            for k, v in cls.__dict__.items()
            if not k.startswith("__") and not callable(v)
        }


# Initialize config to get current values (keep for backward compatibility if needed)
Config.load()

TORTOISE_ORM = {
    "connections": {"default": Config.PG_URL},
    "apps": {
        "models": {
            "models": ["scheduler_service.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}
