"""Misc utility functions."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


def new_uuid() -> uuid.UUID:
    """Return a new UUID4."""
    return uuid.uuid4()


def is_valid_uuid(value: str) -> bool:
    """Return ``True`` if ``value`` is a valid UUID string."""
    try:
        uuid.UUID(value)
        return True
    except (ValueError, TypeError, AttributeError):
        return False


def mask_secret(secret: str, visible: int = 4) -> str:
    """Mask a secret, leaving only the last ``visible`` characters."""
    if not secret:
        return ""
    if len(secret) <= visible:
        return "•" * 8
    return "•" * 8 + secret[-visible:]
