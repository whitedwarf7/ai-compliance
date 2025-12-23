"""JWT token handling."""

import os
from datetime import datetime, timedelta
from typing import Any
import hashlib
import hmac
import base64
import json

from .models import User, Role

# Configuration
JWT_SECRET = os.environ.get("JWT_SECRET", "change-this-secret-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = int(os.environ.get("JWT_EXPIRY_HOURS", "24"))
REFRESH_TOKEN_DAYS = 7


def _base64_url_encode(data: bytes) -> str:
    """Base64 URL-safe encoding without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _base64_url_decode(data: str) -> bytes:
    """Base64 URL-safe decoding."""
    padding = 4 - len(data) % 4
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data)


def _create_signature(message: str, secret: str) -> str:
    """Create HMAC-SHA256 signature."""
    signature = hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).digest()
    return _base64_url_encode(signature)


def create_access_token(user: User) -> str:
    """
    Create a JWT access token for a user.

    Args:
        user: The user to create a token for

    Returns:
        JWT token string
    """
    now = datetime.utcnow()
    exp = now + timedelta(hours=JWT_EXPIRY_HOURS)

    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    payload = {
        "sub": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role.value,
        "org_id": user.org_id,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "type": "access",
    }

    header_encoded = _base64_url_encode(json.dumps(header).encode("utf-8"))
    payload_encoded = _base64_url_encode(json.dumps(payload).encode("utf-8"))

    message = f"{header_encoded}.{payload_encoded}"
    signature = _create_signature(message, JWT_SECRET)

    return f"{message}.{signature}"


def create_refresh_token(user: User) -> str:
    """
    Create a JWT refresh token for a user.

    Args:
        user: The user to create a token for

    Returns:
        JWT refresh token string
    """
    now = datetime.utcnow()
    exp = now + timedelta(days=REFRESH_TOKEN_DAYS)

    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    payload = {
        "sub": user.id,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "type": "refresh",
    }

    header_encoded = _base64_url_encode(json.dumps(header).encode("utf-8"))
    payload_encoded = _base64_url_encode(json.dumps(payload).encode("utf-8"))

    message = f"{header_encoded}.{payload_encoded}"
    signature = _create_signature(message, JWT_SECRET)

    return f"{message}.{signature}"


def verify_token(token: str) -> dict[str, Any] | None:
    """
    Verify and decode a JWT token.

    Args:
        token: The JWT token to verify

    Returns:
        Token payload if valid, None otherwise
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_encoded, payload_encoded, signature = parts

        # Verify signature
        message = f"{header_encoded}.{payload_encoded}"
        expected_signature = _create_signature(message, JWT_SECRET)

        if not hmac.compare_digest(signature, expected_signature):
            return None

        # Decode payload
        payload_json = _base64_url_decode(payload_encoded).decode("utf-8")
        payload = json.loads(payload_json)

        # Check expiration
        exp = payload.get("exp", 0)
        if datetime.utcnow().timestamp() > exp:
            return None

        return payload

    except Exception:
        return None


def get_user_from_token(token: str) -> User | None:
    """
    Get a User object from a JWT token.

    Args:
        token: The JWT token

    Returns:
        User object if token is valid, None otherwise
    """
    payload = verify_token(token)
    if not payload:
        return None

    if payload.get("type") != "access":
        return None

    try:
        return User(
            id=payload["sub"],
            email=payload.get("email", ""),
            name=payload.get("name", ""),
            role=Role(payload.get("role", "viewer")),
            org_id=payload.get("org_id"),
        )
    except Exception:
        return None

