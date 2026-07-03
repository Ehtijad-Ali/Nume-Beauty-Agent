"""Setting schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SettingCreate(BaseModel):
    """Payload to create a setting."""

    key: str = Field(min_length=1, max_length=100)
    value: str | None = None
    category: str = Field(default="general", max_length=50)
    is_sensitive: bool = False
    description: str | None = None


class SettingUpdate(BaseModel):
    """Payload to update a setting."""

    value: str | None = None
    category: str | None = Field(default=None, max_length=50)
    is_sensitive: bool | None = None
    description: str | None = None


class SettingRead(BaseModel):
    """Setting read schema. Sensitive values are masked."""

    id: uuid.UUID
    key: str
    value: str | None = None
    category: str
    is_sensitive: bool
    description: str | None = None
    updated_by_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_model(cls, obj) -> "SettingRead":
        """Build a SettingRead, masking sensitive values."""
        value = obj.value
        if obj.is_sensitive and value:
            value = "••••••••" if len(value) <= 8 else "•" * 8 + value[-4:]
        return cls(
            id=obj.id,
            key=obj.key,
            value=value,
            category=obj.category,
            is_sensitive=obj.is_sensitive,
            description=obj.description,
            updated_by_id=obj.updated_by_id,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )


class SettingBulkUpdate(BaseModel):
    """Bulk update settings."""

    settings: list[SettingUpdate] = Field(min_length=1, max_length=100)
    keys: list[str] = Field(min_length=1, max_length=100)
