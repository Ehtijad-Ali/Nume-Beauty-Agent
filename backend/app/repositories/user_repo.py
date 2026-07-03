"""User repository."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for :class:`User`."""

    model = User

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get_by_email(self, email: str) -> User | None:
        """Return a user by email (case-insensitive)."""
        return self.db.query(User).filter(User.email.ilike(email)).first()

    def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        filters: dict[str, Any] | None = None,
        search: str | None = None,
        search_fields: list[str] | None = None,
        order_by: str | None = None,
        order_dir: str = "asc",
    ) -> tuple[list[User], int]:
        """List users, optionally filtered/searched/sorted."""
        return super().list(
            offset=offset,
            limit=limit,
            filters=filters,
            search=search,
            search_fields=search_fields or ["email", "full_name"],
            order_by=order_by,
            order_dir=order_dir,
        )

    def update_last_login(self, user_id: uuid.UUID) -> None:
        """Set ``last_login_at`` to now for the given user."""
        from datetime import datetime, timezone

        user = self.get(user_id)
        if user:
            user.last_login_at = datetime.now(timezone.utc)
            self.db.flush()
