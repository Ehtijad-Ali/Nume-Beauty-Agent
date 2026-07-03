"""Authentication service — login, register, refresh, logout."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    UnauthorizedError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.security import JWTError
from app.models.session import Session as SessionModel
from app.models.user import User
from app.repositories.role_repo import RoleRepository
from app.repositories.session_repo import SessionRepository
from app.repositories.user_repo import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.user import UserBrief
from app.config.settings import get_settings


class AuthService:
    """Handles authentication flows: register, login, refresh, logout."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.roles = RoleRepository(db)
        self.sessions = SessionRepository(db)

    # ------------------------------------------------------------------ #
    # Register
    # ------------------------------------------------------------------ #
    def register(
        self,
        payload: RegisterRequest,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> User:
        """Register a new user. The first user becomes superuser + admin."""
        if self.users.get_by_email(payload.email):
            raise ConflictError("Email already registered")

        # Determine role
        role = None
        if payload.role:
            role = self.roles.get_by_name(payload.role)
            if role is None:
                raise BadRequestError(f"Unknown role: {payload.role}")
        if role is None:
            role = self.roles.get_by_name("viewer")

        # First user becomes superuser/admin
        is_first = self.db.query(User).count() == 0
        is_superuser = is_first
        if is_first:
            admin_role = self.roles.get_by_name("admin")
            if admin_role:
                role = admin_role

        user = self.users.create(
            {
                "email": payload.email.lower(),
                "full_name": payload.full_name,
                "hashed_password": hash_password(payload.password),
                "is_active": True,
                "is_superuser": is_superuser,
                "role_id": role.id if role else None,
            }
        )
        self.db.commit()
        return user

    # ------------------------------------------------------------------ #
    # Login
    # ------------------------------------------------------------------ #
    def login(
        self,
        payload: LoginRequest,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[User, str, str, datetime]:
        """
        Authenticate a user and return ``(user, access_token, refresh_token, access_expiry)``.
        """
        user = self.users.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")
        if not user.is_active:
            raise UnauthorizedError("Account is deactivated")

        # Tokens
        access_token, access_exp = create_access_token(
            subject=str(user.id),
            extra_claims={
                "email": user.email,
                "role": user.role.name if user.role else None,
                "is_superuser": user.is_superuser,
            },
        )
        refresh_token, refresh_exp = create_refresh_token(subject=str(user.id))

        # Decode refresh JTI for session tracking
        decoded = decode_token(refresh_token)
        self.sessions.create_session(
            user_id=user.id,
            jti=decoded["jti"],
            expires_at=refresh_exp,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        # Update last login
        user.last_login_at = datetime.now(timezone.utc)
        self.db.commit()
        return user, access_token, refresh_token, access_exp

    # ------------------------------------------------------------------ #
    # Refresh
    # ------------------------------------------------------------------ #
    def refresh(self, refresh_token: str) -> tuple[str, str, datetime]:
        """Issue a new access token from a valid refresh token. Returns ``(access, refresh, expiry)``."""
        try:
            decoded = decode_token(refresh_token)
        except JWTError as exc:
            raise UnauthorizedError("Invalid refresh token") from exc

        if decoded.get("type") != "refresh":
            raise UnauthorizedError("Token is not a refresh token")

        session = self.sessions.get_by_jti(decoded["jti"])
        if not session or not session.is_active:
            raise UnauthorizedError("Session expired or revoked")

        user = self.users.get(session.user_id)
        if not user or not user.is_active:
            raise UnauthorizedError("User not found or inactive")

        access_token, access_exp = create_access_token(
            subject=str(user.id),
            extra_claims={
                "email": user.email,
                "role": user.role.name if user.role else None,
                "is_superuser": user.is_superuser,
            },
        )
        return access_token, refresh_token, access_exp

    # ------------------------------------------------------------------ #
    # Logout
    # ------------------------------------------------------------------ #
    def logout(self, refresh_token: str) -> bool:
        """Revoke the session associated with a refresh token."""
        try:
            decoded = decode_token(refresh_token)
        except JWTError:
            # Silently succeed — caller doesn't care, they want logged-out state.
            return True
        if decoded.get("type") != "refresh":
            return True
        self.sessions.revoke(decoded["jti"])
        self.db.commit()
        return True

    # ------------------------------------------------------------------ #
    # Logout everywhere
    # ------------------------------------------------------------------ #
    def logout_everywhere(self, user_id: uuid.UUID) -> int:
        """Revoke every active session for a user."""
        count = self.sessions.revoke_all_for_user(user_id)
        self.db.commit()
        return count

    # ------------------------------------------------------------------ #
    # Build user brief
    # ------------------------------------------------------------------ #
    @staticmethod
    def build_user_brief(user: User) -> UserBrief:
        """Build a :class:`UserBrief` from a user model."""
        return UserBrief.model_validate(user)
