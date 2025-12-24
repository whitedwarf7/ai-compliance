"""Authentication models."""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import uuid


class Role(str, Enum):
    """User roles with different permission levels."""

    ADMIN = "admin"  # Full access to all features
    ANALYST = "analyst"  # Read + export capabilities
    VIEWER = "viewer"  # Read-only access


class Permission(str, Enum):
    """Granular permissions for RBAC."""

    VIEW_LOGS = "view_logs"
    EXPORT_LOGS = "export_logs"
    VIEW_VIOLATIONS = "view_violations"
    EXPORT_VIOLATIONS = "export_violations"
    MANAGE_POLICIES = "manage_policies"
    MANAGE_USERS = "manage_users"
    VIEW_SETTINGS = "view_settings"
    MANAGE_SETTINGS = "manage_settings"


# Role to permissions mapping
ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.ADMIN: set(Permission),  # All permissions
    Role.ANALYST: {
        Permission.VIEW_LOGS,
        Permission.EXPORT_LOGS,
        Permission.VIEW_VIOLATIONS,
        Permission.EXPORT_VIOLATIONS,
        Permission.VIEW_SETTINGS,
    },
    Role.VIEWER: {
        Permission.VIEW_LOGS,
        Permission.VIEW_VIOLATIONS,
        Permission.VIEW_SETTINGS,
    },
}


@dataclass
class User:
    """User model for authentication."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    email: str = ""
    name: str = ""
    role: Role = Role.VIEWER
    org_id: str | None = None
    avatar: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has a specific permission."""
        return permission in ROLE_PERMISSIONS.get(self.role, set())

    def to_dict(self) -> dict[str, Any]:
        """Convert user to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "role": self.role.value,
            "org_id": self.org_id,
            "avatar": self.avatar,
        }


@dataclass
class TokenPair:
    """JWT token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600  # 1 hour


@dataclass
class UserCredentials:
    """Login credentials."""

    email: str
    password: str


# Demo users for pilot mode
DEMO_USERS: dict[str, User] = {
    "admin@demo.com": User(
        id="demo-admin",
        email="admin@demo.com",
        name="Demo Admin",
        role=Role.ADMIN,
        org_id="demo-org",
    ),
    "analyst@demo.com": User(
        id="demo-analyst",
        email="analyst@demo.com",
        name="Demo Analyst",
        role=Role.ANALYST,
        org_id="demo-org",
    ),
    "viewer@demo.com": User(
        id="demo-viewer",
        email="viewer@demo.com",
        name="Demo Viewer",
        role=Role.VIEWER,
        org_id="demo-org",
    ),
}


