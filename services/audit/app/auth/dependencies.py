"""FastAPI dependencies for authentication."""

from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .jwt import get_user_from_token
from .models import User, Permission, ROLE_PERMISSIONS

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> User | None:
    """
    Get the current authenticated user from the JWT token.

    Returns None if no valid token is provided (for optional auth).
    """
    if not credentials:
        return None

    token = credentials.credentials
    user = get_user_from_token(token)

    return user


async def require_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> User:
    """
    Require authentication. Raises 401 if not authenticated.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_permission(permission: Permission) -> Callable:
    """
    Dependency factory that requires a specific permission.

    Usage:
        @router.get("/admin")
        async def admin_only(user: User = Depends(require_permission(Permission.MANAGE_USERS))):
            ...
    """
    async def _check_permission(
        user: User = Depends(require_auth),
    ) -> User:
        if not user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission.value} required",
            )
        return user

    return _check_permission


def require_role(min_role: str) -> Callable:
    """
    Dependency factory that requires a minimum role level.

    Roles hierarchy: viewer < analyst < admin
    """
    role_levels = {"viewer": 0, "analyst": 1, "admin": 2}

    async def _check_role(
        user: User = Depends(require_auth),
    ) -> User:
        user_level = role_levels.get(user.role.value, 0)
        required_level = role_levels.get(min_role, 0)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{min_role}' or higher required",
            )
        return user

    return _check_role


