"""Setting service."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.setting import Setting
from app.repositories.setting_repo import SettingRepository
from app.schemas.setting import SettingCreate, SettingUpdate


class SettingService:
    """Business logic for workspace settings."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = SettingRepository(db)

    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 100,
        search: str | None = None,
        category: str | None = None,
    ) -> tuple[list[Setting], int]:
        """List settings with optional filters."""
        filters: dict[str, Any] = {}
        if category:
            filters["category"] = category
        return self.repo.list(
            offset=(page - 1) * page_size,
            limit=page_size,
            filters=filters,
            search=search,
        )

    def get(self, setting_id: uuid.UUID) -> Setting:
        """Return a setting by ID or raise."""
        s = self.repo.get(setting_id)
        if not s:
            raise NotFoundError("Setting not found")
        return s

    def get_by_key(self, key: str) -> Setting:
        """Return a setting by key or raise."""
        s = self.repo.get_by_key(key)
        if not s:
            raise NotFoundError(f"Setting '{key}' not found")
        return s

    def create(
        self,
        payload: SettingCreate,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> Setting:
        """Create a new setting."""
        data = payload.model_dump()
        if actor_id:
            data["updated_by_id"] = actor_id
        setting = self.repo.create(data)
        self.db.commit()
        return setting

    def upsert(
        self,
        key: str,
        value: str | None,
        *,
        category: str = "general",
        is_sensitive: bool = False,
        description: str | None = None,
        actor_id: uuid.UUID | None = None,
    ) -> Setting:
        """Insert or update a setting by key."""
        setting = self.repo.upsert(
            key=key,
            value=value,
            category=category,
            is_sensitive=is_sensitive,
            description=description,
        )
        if actor_id:
            setting.updated_by_id = actor_id
        self.db.commit()
        return setting

    def update(
        self,
        setting_id: uuid.UUID,
        payload: SettingUpdate,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> Setting:
        """Update a setting by ID."""
        setting = self.get(setting_id)
        data = payload.model_dump(exclude_unset=True)
        if actor_id:
            data["updated_by_id"] = actor_id
        updated = self.repo.update(setting, data)
        self.db.commit()
        return updated

    def delete(self, setting_id: uuid.UUID) -> None:
        """Delete a setting."""
        setting = self.get(setting_id)
        self.repo.delete(setting)
        self.db.commit()
