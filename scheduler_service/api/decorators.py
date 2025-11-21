from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from scheduler_service.models import User

# 创建Bearer认证方案
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """获取当前认证用户"""
    token = credentials.credentials

    # 从token中验证用户
    # 这里需要调整User.verify_auth_token方法以适应FastAPI
    user = await User.verify_auth_token(token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


# 保留login_require名称以兼容现有代码
login_require = get_current_user