from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from tortoise.exceptions import DoesNotExist, IntegrityError

from scheduler_service.api.decorators import login_require
from scheduler_service.models import User


# Pydantic models
def to_camel(string: str) -> str:
    """Convert snake_case to camelCase"""
    components = string.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


class UserCreate(BaseModel):
    """User creation model"""
    name: str
    password: str
    email: EmailStr


class UserUpdate(BaseModel):
    """User update model"""
    name: str | None = None
    email: EmailStr | None = None
    password: str | None = None


class UserResponse(BaseModel):
    """User response model"""
    id: int
    name: str
    email: str

    class Config:
        """Pydantic configuration"""
        from_attributes = True


class TokenRequest(BaseModel):
    """Token request model"""
    name: str | None = None
    email: str | None = None
    password: str


class TokenResponse(BaseModel):
    """Token response model"""
    token: str


async def create_user(user_data: UserCreate):
    """Create new user"""
    try:
        # Create user
        password_hash = User.hash_password(user_data.password)
        user = await User.create(
            name=user_data.name,
            password_hash=password_hash,
            email=user_data.email
        )
        return {'uid': user.id}
    except IntegrityError as e:
        if "name" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            ) from e
        elif "email" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            ) from e
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            ) from e


async def get_current_user_info(current_user: User = Depends(login_require)):
    """Get current user info"""
    return current_user.to_dict()


async def update_user(user_data: UserUpdate, current_user: User = Depends(login_require)):
    """Update user info"""
    update_data = {}

    # Handle password update
    if user_data.password:
        update_data['password_hash'] = User.hash_password(user_data.password)

    # Handle other fields update
    if user_data.name:
        update_data['name'] = user_data.name
    if user_data.email:
        update_data['email'] = user_data.email

    # Execute update
    if update_data:
        try:
            await User.filter(id=current_user.id).update(**update_data)
        except IntegrityError as e:
            if "name" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists"
                ) from e
            elif "email" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                ) from e
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update user info"
                ) from e

        # Re-fetch updated user info
        updated_user = await User.get(id=current_user.id)
        return updated_user.to_dict()

    return current_user.to_dict()


async def delete_user(current_user: User = Depends(login_require)):
    """Delete current user"""
    await current_user.delete()
    return {"message": "User deleted"}


async def get_token(token_data: TokenRequest, request: Request):
    """Get authentication token"""
    # Validate request parameters
    if not token_data.name and not token_data.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please enter username or email"
        )

    try:
        # Find user by username or email
        if token_data.name:
            user = await User.get(name=token_data.name)
        else:
            user = await User.get(email=token_data.email)
    except DoesNotExist as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    # Verify password
    if not user.verify_password(token_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update login time
    await user.ping()

    # Generate token
    secret_key = request.app.config.get("SECRET_KEY")
    token = user.generate_auth_token(secret_key)

    return {"token": token}

router = APIRouter()

# User management
router.add_api_route("", create_user, methods=["POST"])
router.add_api_route("/me", get_current_user_info, methods=["GET"])
router.add_api_route("/me", update_user, methods=["PUT"])
router.add_api_route("/me", delete_user, methods=["DELETE"])

# Token
router.add_api_route("/token", get_token, methods=["POST"])
