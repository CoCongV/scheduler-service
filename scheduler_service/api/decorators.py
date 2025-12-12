from typing import Optional

from fastapi import Depends, HTTPException, Request, status  # Added Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from scheduler_service.models import User, ApiKey

# Create Bearer authentication scheme
security = HTTPBearer(auto_error=False)


async def login_require(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    """Get current authenticated user via Bearer Token or API Key"""

    # 1. Try Bearer Token
    if credentials:
        token = credentials.credentials
        secret_key = request.app.config.get("SECRET_KEY")
        user = await User.verify_auth_token(token, secret_key)
        if user:
            return user

    # 2. Try API Key
    api_key_header = request.headers.get("X-API-KEY")
    if api_key_header:
        # Key format: prefix... (we need to find by prefix first for efficiency, or just iterate)
        # Since we don't enforce prefix in header, we can just search by prefix if we assume standard format,
        # or we can try to match against all active keys.
        # Optimization: Client sends raw key. We extract prefix (first 8 chars).
        if len(api_key_header) > 8:
            prefix = api_key_header[:8]
            # Find potential keys with this prefix
            potential_keys = await ApiKey.filter(prefix=prefix, is_active=True).prefetch_related("user")
            for key_obj in potential_keys:
                if key_obj.verify_key(api_key_header):
                    return key_obj.user

    # 3. Unauthorized
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized",
        headers={"WWW-Authenticate": "Bearer"},
    )
