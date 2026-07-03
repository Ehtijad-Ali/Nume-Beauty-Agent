"""Authentication-related schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Login request payload."""

    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class RegisterRequest(BaseModel):
    """Registration request payload."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    role: str | None = Field(default="viewer", description="Optional role name")


class RefreshRequest(BaseModel):
    """Token refresh request payload."""

    refresh_token: str


class LogoutRequest(BaseModel):
    """Logout request payload."""

    refresh_token: str


class TokenResponse(BaseModel):
    """Token response containing access + refresh tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token lifetime in seconds")
    expires_at: datetime
    user: "UserBrief"  # forward ref

    model_config = {"from_attributes": True}


from app.schemas.user import UserBrief  # noqa: E402

TokenResponse.model_rebuild()
