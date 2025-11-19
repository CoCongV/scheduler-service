# Tortoise-ORM models initialization

from .user import User
from .task import Task, URLDetail

__all__ = [
    'User', 'Task', 'URLDetail'
]