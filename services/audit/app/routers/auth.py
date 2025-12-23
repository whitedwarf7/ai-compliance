"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from ..auth import (
    User,
    Role,
    TokenPair,
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user,
    require_permission,
    Permission,
)
from ..auth.models import DEMO_USERS
from ..auth.jwt import get_user_from_token

router = APIRouter()


class LoginRequest(BaseModel):
    """Login request body."""

    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response."""

    user: dict
    token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str


class UserResponse(BaseModel):
    """User response."""

    id: str
    email: str
    name: str
    role: str
    org_id: str | None = None
    avatar: str | None = None


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT tokens.

    For demo mode, any password works with demo user emails.
    """
    email = request.email.lower()

    # Check demo users
    if email in DEMO_USERS:
        user = DEMO_USERS[email]
        # In demo mode, accept any password
        access_token = create_access_token(user)
        refresh_token = create_refresh_token(user)

        return LoginResponse(
            user=user.to_dict(),
            token=access_token,
            refresh_token=refresh_token,
        )

    # In production, verify against database
    # For now, reject unknown users
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
    )


@router.post("/logout")
async def logout(user: User = Depends(get_current_user)):
    """
    Logout user (invalidate token).

    Note: JWT tokens are stateless, so this just returns success.
    In production, implement token blacklisting.
    """
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(request: RefreshRequest):
    """
    Refresh access token using refresh token.
    """
    payload = verify_token(request.refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")

    # Find user (check demo users for now)
    user = None
    for demo_user in DEMO_USERS.values():
        if demo_user.id == user_id:
            user = demo_user
            break

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    access_token = create_access_token(user)
    new_refresh_token = create_refresh_token(user)

    return LoginResponse(
        user=user.to_dict(),
        token=access_token,
        refresh_token=new_refresh_token,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    """
    Get current authenticated user.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role.value,
        org_id=user.org_id,
        avatar=user.avatar,
    )


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    user: User = Depends(require_permission(Permission.MANAGE_USERS)),
):
    """
    List all users (admin only).
    """
    # Return demo users for now
    return [
        UserResponse(
            id=u.id,
            email=u.email,
            name=u.name,
            role=u.role.value,
            org_id=u.org_id,
            avatar=u.avatar,
        )
        for u in DEMO_USERS.values()
    ]

