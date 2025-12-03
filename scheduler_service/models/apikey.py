import secrets
from datetime import datetime

from passlib.hash import pbkdf2_sha256
from tortoise import fields
from tortoise.models import Model

from .user import User


class ApiKey(Model):
    """API Key model for third-party access"""
    id = fields.IntField(pk=True)
    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="api_keys", description="Owner of the API key"
    )
    key_hash = fields.CharField(max_length=256, description="Hashed API key")
    prefix = fields.CharField(
        max_length=8, description="Key prefix for identification")
    name = fields.CharField(
        max_length=64, description="Friendly name for the key")
    created_at = fields.DatetimeField(auto_now_add=True)
    expires_at = fields.DatetimeField(
        null=True, description="Expiration time (optional)")
    is_active = fields.BooleanField(
        default=True, description="Whether the key is active")

    class Meta:
        table = "api_keys"

    @staticmethod
    def generate_key() -> str:
        """Generate a random API key"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_key(key: str) -> str:
        """Hash the API key"""
        return pbkdf2_sha256.hash(key)

    def verify_key(self, key: str) -> bool:
        """Verify the API key against the hash"""
        return pbkdf2_sha256.verify(key, self.key_hash)
