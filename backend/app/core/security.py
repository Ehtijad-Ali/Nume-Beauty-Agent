"""
Security utilities — password hashing and JWT token management.

Uses Passlib (bcrypt) for password hashing and python-jose for JWT signing.
Both access and refresh tokens are JWTs; refresh tokens carry a ``type: refresh``
claim so the backend can distinguish them from access tokens.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config.settings import get_settings

# --------------------------------------------------------------------------- #
# Password hashing
# --------------------------------------------------------------------------- #

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_password(plain: str) -> str:
    """Return a bcrypt hash for the given plaintext password."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return ``True`` if ``plain`` matches ``hashed``."""
    try:
        return _pwd_context.verify(plain, hashed)
    except (ValueError, TypeError):
        return False


# --------------------------------------------------------------------------- #
# JWT
# --------------------------------------------------------------------------- #

TokenSubject = Literal["access", "refresh"]


def _create_token(
    subject: str,
    token_type: TokenSubject,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> tuple[str, datetime]:
    """Create a signed JWT and return ``(token, expiry_datetime)``."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": uuid.uuid4().hex,
    }
    if extra_claims:
        payload.update(extra_claims)
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expire


def create_access_token(
    subject: str,
    extra_claims: dict[str, Any] | None = None,
) -> tuple[str, datetime]:
    """Create a short-lived access token."""
    settings = get_settings()
    return _create_token(
        subject,
        "access",
        timedelta(minutes=settings.access_token_expire_minutes),
        extra_claims,
    )


def create_refresh_token(
    subject: str,
    extra_claims: dict[str, Any] | None = None,
) -> tuple[str, datetime]:
    """Create a long-lived refresh token."""
    settings = get_settings()
    return _create_token(
        subject,
        "refresh",
        timedelta(days=settings.refresh_token_expire_days),
        extra_claims,
    )


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and verify a JWT.

    Raises :class:`JWTError` on invalid signature, expired token or malformed
    payload.
    """
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


__all__ = [
    "JWTError",
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
]
