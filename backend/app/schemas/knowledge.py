"""Knowledge document schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class KnowledgeDocumentCreate(BaseModel):
    """Payload to create a knowledge document."""

    title: str = Field(min_length=1, max_length=500)
    doc_type: str = Field(min_length=1, max_length=20)
    source_url: str | None = None
    file_path: str | None = None
    file_size: int = Field(default=0, ge=0)
    checksum: str | None = None
    tags: str | None = None
    excerpt: str | None = None
    status: str = Field(default="queued", pattern="^(queued|processing|ready|failed)$")


class KnowledgeDocumentUpdate(BaseModel):
    """Payload to update a knowledge document. All fields optional."""

    title: str | None = Field(default=None, max_length=500)
    doc_type: str | None = None
    source_url: str | None = None
    file_path: str | None = None
    file_size: int | None = Field(default=None, ge=0)
    checksum: str | None = None
    tags: str | None = None
    excerpt: str | None = None
    status: str | None = Field(default=None, pattern="^(queued|processing|ready|failed)$")


class KnowledgeDocumentRead(BaseModel):
    """Knowledge document read schema."""

    id: uuid.UUID
    title: str
    doc_type: str
    source_url: str | None = None
    file_path: str | None = None
    file_size: int
    checksum: str | None = None
    status: str
    tags: str | None = None
    excerpt: str | None = None
    uploaded_by_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
