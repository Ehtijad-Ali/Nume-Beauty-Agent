"""Setting repository."""

from __future__ import annotations

from typing import Any

from app.models.setting import Setting
from app.repositories.base import BaseRepository


class SettingRepository(BaseRepository[Setting]):
    """Repository for :class:`Setting`."""

    model = Setting

    def get_by_key(self, key: str) -> Setting | None:
        """Return a setting by its unique key."""
        return self.db.query(Setting).filter(Setting.key == key).first()

    def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        filters: dict[str, Any] | None = None,
        search: str | None = None,
        search_fields: list[str] | None = None,
        order_by: str | None = None,
        order_dir: str = "asc",
    ) -> tuple[list[Setting], int]:
        return super().list(
            offset=offset,
            limit=limit,
            filters=filters,
            search=search,
            search_fields=search_fields or ["key", "category"],
            order_by=order_by or "key",
            order_dir=order_dir,
        )

    def upsert(self, key: str, value: str | None, **kwargs: Any) -> Setting:
        """Insert or update a setting by key."""
        setting = self.get_by_key(key)
        if setting is None:
            data = {"key": key, "value": value, **kwargs}
            return self.create(data)
        if value is not None:
            setting.value = value
        for k, v in kwargs.items():
            if hasattr(setting, k):
                setattr(setting, k, v)
        self.db.flush()
        self.db.refresh(setting)
        return setting
