"""Authentication endpoints: login, register, refresh, logout."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_user
from app.dependencies.database import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.common import MessageResponse
from app.schemas.user import UserRead
from app.services.auth_service import AuthService

router = APIRouter()


def _client_meta(request: Request) -> dict:
    """Extract client IP + User-Agent for session tracking."""
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
    }


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new account",
)
def register(
    payload: RegisterRequest,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Register a new user. The first user becomes the superuser/admin."""
    service = AuthService(db)
    return service.register(payload)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login",
)
def login(
    payload: LoginRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Authenticate with email + password and receive JWT tokens."""
    service = AuthService(db)
    meta = _client_meta(request)
    user, access, refresh, exp = service.login(
        payload, user_agent=meta["user_agent"], ip_address=meta["ip_address"]
    )
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": int((exp - _now_utc()).total_seconds()),
        "expires_at": exp,
        "user": user,
    }


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
def refresh(
    payload: RefreshRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Exchange a valid refresh token for a new access token."""
    service = AuthService(db)
    access, refresh, exp = service.refresh(payload.refresh_token)
    user_id = _user_id_from_refresh(payload.refresh_token)
    from app.repositories.user_repo import UserRepository

    user = UserRepository(db).get(user_id)
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": int((exp - _now_utc()).total_seconds()),
        "expires_at": exp,
        "user": user,
    }


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout",
)
def logout(
    payload: LogoutRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Revoke the session associated with the refresh token."""
    service = AuthService(db)
    service.logout(payload.refresh_token)
    return {"message": "Logged out"}


@router.post(
    "/logout-all",
    response_model=MessageResponse,
    summary="Logout from all devices",
)
def logout_all(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """Revoke every active session for the authenticated user."""
    service = AuthService(db)
    count = service.logout_everywhere(user.id)
    return {"message": f"Revoked {count} session(s)"}


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current user",
)
def me(user: Annotated[User, Depends(get_current_active_user)]) -> User:
    """Return the currently authenticated user's profile."""
    return user


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _now_utc():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc)


def _user_id_from_refresh(refresh_token: str) -> uuid.UUID:
    """Decode a refresh token and return the user id as a UUID."""
    from app.core.security import decode_token

    payload = decode_token(refresh_token)
    return uuid.UUID(payload["sub"])
