from datetime import datetime

import jwt
from passlib.hash import pbkdf2_sha256
from tortoise.models import Model
from tortoise import fields


class User(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=32)
    password_hash = fields.CharField(max_length=256)
    email = fields.CharField(max_length=32)
    verify = fields.BooleanField(default=False)
    register_time = fields.DatetimeField(auto_now_add=True)
    login_time = fields.DatetimeField(null=True)

    async def ping(self):
        await self.update(login_time=datetime.now())

    @property
    def password(self):
        raise AttributeError('password is not a readable attr')

    @password.setter
    def password(self, password):
        self.password_hash = pbkdf2_sha256.hash(password)

    @staticmethod
    def hash_password(password: str) -> str:
        return pbkdf2_sha256.hash(password)

    def verify_password(self, password: str) -> bool:
        return pbkdf2_sha256.verify(password, self.password_hash)

    def generate_auth_token(self) -> str:
        from scheduler_service.config import Config
        return jwt.encode({'id': self.id, 'flag': 'auth'},
                          Config.SECRET_KEY,
                          algorithm='HS256')

    @classmethod
    async def verify_auth_token(cls, token: str):
        from scheduler_service.config import Config
        try:
            data = jwt.decode(token,
                              Config.SECRET_KEY,
                              algorithms=['HS256'])
        except Exception:
            return False
        else:
            if data['flag'] != 'auth':
                return False
            try:
                return await cls.get(id=data['id'])
            except cls.DoesNotExist:
                return False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email
        }