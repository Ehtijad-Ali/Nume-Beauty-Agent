"""User service."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.core.security import hash_password
from app.models.user import User
from app.repositories.role_repo import RoleRepository
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """Business logic for user management."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.roles = RoleRepository(db)

    def list_users(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        is_active: bool | None = None,
        role_id: uuid.UUID | None = None,
    ) -> tuple[list[User], int]:
        """List users with pagination + filters."""
        filters: dict[str, Any] = {}
        if is_active is not None:
            filters["is_active"] = is_active
        if role_id is not None:
            filters["role_id"] = role_id
        return self.users.list(
            offset=(page - 1) * page_size,
            limit=page_size,
            filters=filters,
            search=search,
        )

    def get(self, user_id: uuid.UUID) -> User:
        """Return a user by ID or raise."""
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        return user

    def create(self, payload: UserCreate, *, actor_id: uuid.UUID | None = None) -> User:
        """Create a new user."""
        if self.users.get_by_email(payload.email):
            raise ConflictError("Email already registered")

        role_id = payload.role_id
        if role_id is None:
            viewer_role = self.roles.get_by_name("viewer")
            role_id = viewer_role.id if viewer_role else None

        user = self.users.create(
            {
                "email": payload.email.lower(),
                "full_name": payload.full_name,
                "hashed_password": hash_password(payload.password),
                "is_active": payload.is_active,
                "is_superuser": False,
                "role_id": role_id,
            }
        )
        self.db.commit()
        return user

    def update(self, user_id: uuid.UUID, payload: UserUpdate) -> User:
        """Update an existing user."""
        user = self.get(user_id)
        data = payload.model_dump(exclude_unset=True)

        # Prevent email collision if email were ever added to update schema
        if "role_id" in data and data["role_id"] is not None:
            if not self.roles.get(data["role_id"]):
                raise BadRequestError("Invalid role_id")

        updated = self.users.update(user, data)
        self.db.commit()
        return updated

    def delete(self, user_id: uuid.UUID, *, actor_id: uuid.UUID | None = None) -> None:
        """Delete a user. Prevents self-deletion and superuser deletion."""
        if actor_id and user_id == actor_id:
            raise BadRequestError("You cannot delete your own account")
        user = self.get(user_id)
        if user.is_superuser:
            raise BadRequestError("Superuser accounts cannot be deleted")
        self.users.delete(user)
        self.db.commit()

    def set_password(self, user_id: uuid.UUID, new_password: str) -> None:
        """Set a new password for a user."""
        user = self.get(user_id)
        user.hashed_password = hash_password(new_password)
        self.db.commit()
