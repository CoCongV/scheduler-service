from pydantic import BaseModel
from fastapi import HTTPException, status
from tortoise.exceptions import DoesNotExist
from scheduler_service.models import User


class TokenRequest(BaseModel):
    """Token请求模型"""
    name: str | None = None
    email: str | None = None
    password: str


class TokenResponse(BaseModel):
    """Token响应模型"""
    token: str


async def get_token(token_data: TokenRequest):
    """获取认证token"""
    # 验证请求参数
    if not token_data.name and not token_data.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请输入用户名或邮箱"
        )

    try:
        # 根据用户名或邮箱查找用户
        if token_data.name:
            user = await User.get(name=token_data.name)
        else:
            user = await User.get(email=token_data.email)
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 验证密码
    if not user.verify_password(token_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 更新登录时间
    await user.ping()

    # 生成token
    token = user.generate_auth_token()

    return {"token": token}