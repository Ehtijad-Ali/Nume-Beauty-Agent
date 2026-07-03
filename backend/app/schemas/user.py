"""User schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.role import RoleRead


class UserBrief(BaseModel):
    """Minimal user info (used in tokens, audit logs, etc.)."""

    id: uuid.UUID
    email: EmailStr
    full_name: str
    avatar_url: str | None = None
    role: RoleRead | None = None

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    """Payload to create a user."""

    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role_id: uuid.UUID | None = None
    is_active: bool = True

    @field_validator("password")
    @classmethod
    def _strong_password(cls, v: str) -> str:
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        return v


class UserUpdate(BaseModel):
    """Payload to update a user. All fields optional."""

    full_name: str | None = Field(default=None, max_length=255)
    avatar_url: str | None = None
    bio: str | None = None
    is_active: bool | None = None
    role_id: uuid.UUID | None = None


class UserRead(BaseModel):
    """User read schema."""

    id: uuid.UUID
    email: EmailStr
    full_name: str
    avatar_url: str | None = None
    bio: str | None = None
    is_active: bool
    is_superuser: bool
    last_login_at: datetime | None = None
    role: RoleRead | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserList(BaseModel):
    """User list item (same as UserRead for now)."""

    id: uuid.UUID
    email: EmailStr
    full_name: str
    avatar_url: str | None = None
    is_active: bool
    is_superuser: bool
    role: RoleRead | None = None
    last_login_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
