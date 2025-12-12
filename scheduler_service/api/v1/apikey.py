from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from scheduler_service.api.decorators import login_require
from scheduler_service.models import ApiKey, User


class ApiKeyCreate(BaseModel):
    name: str


class ApiKeyResponse(BaseModel):
    id: int
    prefix: str
    name: str
    created_at: str
    is_active: bool


class ApiKeyCreatedResponse(ApiKeyResponse):
    key: str  # Only returned once upon creation


async def create_api_key(
    data: ApiKeyCreate,
    current_user: User = Depends(login_require)
) -> ApiKeyCreatedResponse:
    """Generate a new API key"""
    raw_key = ApiKey.generate_key()
    key_hash = ApiKey.hash_key(raw_key)
    prefix = raw_key[:8]

    api_key = await ApiKey.create(
        user=current_user,
        key_hash=key_hash,
        prefix=prefix,
        name=data.name
    )

    return ApiKeyCreatedResponse(
        id=api_key.id,
        prefix=api_key.prefix,
        name=api_key.name,
        created_at=str(api_key.created_at),
        is_active=api_key.is_active,
        key=raw_key
    )


async def list_api_keys(
    current_user: User = Depends(login_require)
) -> List[ApiKeyResponse]:
    """List active API keys"""
    keys = await ApiKey.filter(user=current_user, is_active=True).all()
    return [
        ApiKeyResponse(
            id=k.id,
            prefix=k.prefix,
            name=k.name,
            created_at=str(k.created_at),
            is_active=k.is_active
        )
        for k in keys
    ]


async def revoke_api_key(
    key_id: int,
    current_user: User = Depends(login_require)
):
    """Revoke an API key"""
    key = await ApiKey.get_or_none(id=key_id, user=current_user)
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    key.is_active = False
    await key.save()
    return {"message": "API key revoked"}


router = APIRouter()
router.add_api_route("", create_api_key, methods=[
                     "POST"], response_model=ApiKeyCreatedResponse)
router.add_api_route("", list_api_keys, methods=[
                     "GET"], response_model=List[ApiKeyResponse])
router.add_api_route("/{key_id}", revoke_api_key, methods=["DELETE"])
