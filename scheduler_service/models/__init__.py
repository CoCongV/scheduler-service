# Tortoise-ORM models initialization

from .user import User
from .task import RequestTask, URLDetail

__all__ = [
    'User', 'RequestTask', 'URLDetail'
]