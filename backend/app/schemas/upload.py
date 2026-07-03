"""Upload schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class UploadCreate(BaseModel):
    """Payload to register an upload (after the file has been stored)."""

    filename: str = Field(min_length=1, max_length=512)
    original_filename: str = Field(min_length=1, max_length=512)
    mime_type: str = Field(min_length=1, max_length=255)
    size: int = Field(ge=0)
    storage_path: str = Field(min_length=1, max_length=1024)
    storage_type: str = Field(default="local", max_length=20)
    category: str = Field(default="other", max_length=50)
    status: str = Field(default="completed", pattern="^(queued|uploading|completed|failed)$")
    checksum: str | None = None
    description: str | None = None


class UploadUpdate(BaseModel):
    """Payload to update an upload record."""

    category: str | None = Field(default=None, max_length=50)
    status: str | None = Field(default=None, pattern="^(queued|uploading|completed|failed)$")
    description: str | None = None


class UploadRead(BaseModel):
    """Upload read schema."""

    id: uuid.UUID
    filename: str
    original_filename: str
    mime_type: str
    size: int
    storage_path: str
    storage_type: str
    category: str
    status: str
    checksum: str | None = None
    description: str | None = None
    uploaded_by_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
