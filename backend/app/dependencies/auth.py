"""
Authentication & authorisation dependencies.

Exposes:
  * :func:`get_current_user`         — decode JWT, return user (or 401)
  * :func:`get_current_active_user`  — same, but inactive accounts get 401
  * :func:`require_role(name)`       — single role required
  * :func:`require_roles(*names)`    — any of the listed roles required
  * :func:`require_superuser`        — superuser-only access
  * :class:`RoleChecker`             — class-based role guard for advanced use
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Sequence
from typing import Annotated

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import JWTError, decode_token
from app.dependencies.database import get_db
from app.models.user import User
from app.repositories.user_repo import UserRepository

# Bearer token extractor
_bearer = HTTPBearer(auto_error=False)


def _extract_token(
    credentials: HTTPAuthorizationCredentials | None,
    authorization: str | None,
) -> str:
    """Pull the raw token from the Bearer header."""
    if credentials and credentials.credentials:
        return credentials.credentials
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    raise UnauthorizedError("Missing authentication token")


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    """Decode the JWT and return the active :class:`User`."""
    token = _extract_token(credentials, authorization)

    try:
        payload = decode_token(token)
    except JWTError as exc:
        raise UnauthorizedError("Invalid or expired token") from exc

    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Token missing subject")

    user = UserRepository(db).get(uuid.UUID(user_id))
    if user is None:
        raise UnauthorizedError("User not found")

    return user


def get_current_active_user(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Ensure the authenticated user is active."""
    if not user.is_active:
        raise UnauthorizedError("Account is deactivated")
    return user


def require_roles(*allowed_roles: str) -> Callable[[User], User]:
    """
    Return a FastAPI dependency that allows any of the listed roles.

    Superusers bypass role checks. Usage::

        @router.post("/", dependencies=[Depends(require_roles("admin"))])
        def create(...): ...
    """

    def _checker(user: Annotated[User, Depends(get_current_active_user)]) -> User:
        if user.is_superuser:
            return user
        if not user.role or user.role.name not in set(allowed_roles):
            raise ForbiddenError(
                f"Requires one of roles: {', '.join(sorted(allowed_roles))}"
            )
        return user

    # Tag the closure so it's introspectable
    _checker.__name__ = f"require_roles_{'_'.join(allowed_roles)}"
    return _checker


def require_role(role_name: str) -> Callable[[User], User]:
    """Return a FastAPI dependency that requires a single role."""
    return require_roles(role_name)


class RoleChecker:
    """Class-based role guard (advanced use). Prefer :func:`require_roles`."""

    def __init__(self, allowed_roles: Sequence[str], *, require_superuser: bool = False) -> None:
        self.allowed_roles = set(allowed_roles)
        self.require_superuser_flag = require_superuser
        # Pre-build a closure-based checker that FastAPI can introspect.
        self._checker = require_roles(*allowed_roles)

    def __call__(self, user: Annotated[User, Depends(get_current_active_user)]) -> User:
        """Validate the user's role against the allowed set."""
        if self.require_superuser_flag and not user.is_superuser:
            raise ForbiddenError("Superuser access required")
        return self._checker(user)


def require_superuser(
    user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """Dependency that requires superuser privileges."""
    if not user.is_superuser:
        raise ForbiddenError("Superuser access required")
    return user
