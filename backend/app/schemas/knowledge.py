"""Knowledge document schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------- #
# Categories
# --------------------------------------------------------------------------- #


class CategoryCreate(BaseModel):
    """Payload to create a category."""

    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    color: str | None = Field(default=None, max_length=20)


class CategoryUpdate(BaseModel):
    """Payload to update a category. All fields optional."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    color: str | None = Field(default=None, max_length=20)


class CategoryRead(BaseModel):
    """Category read schema."""

    id: uuid.UUID
    name: str
    slug: str
    description: str | None = None
    color: str | None = None
    document_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --------------------------------------------------------------------------- #
# Documents
# --------------------------------------------------------------------------- #


class UserBrief(BaseModel):
    """Minimal user info embedded in document responses."""

    id: uuid.UUID
    full_name: str
    email: str

    model_config = {"from_attributes": True}


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
    brand: str | None = Field(default=None, max_length=200)
    category_id: uuid.UUID | None = None


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
    brand: str | None = Field(default=None, max_length=200)
    category_id: uuid.UUID | None = None


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
    original_filename: str | None = None
    mime_type: str | None = None
    brand: str | None = None
    version: int = 1
    language: str | None = None
    page_count: int | None = None
    word_count: int | None = None
    char_count: int | None = None
    chunk_count: int = 0
    doc_metadata: dict[str, Any] | None = None
    error_message: str | None = None
    last_indexed_at: datetime | None = None
    embedding_status: str = "none"
    embedding_error: str | None = None
    embedding_model: str | None = None
    embedded_at: datetime | None = None
    vector_count: int = 0
    category_id: uuid.UUID | None = None
    category: CategoryRead | None = None
    uploaded_by_id: uuid.UUID | None = None
    uploaded_by: UserBrief | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --------------------------------------------------------------------------- #
# Versions & chunks
# --------------------------------------------------------------------------- #


class DocumentVersionRead(BaseModel):
    """Document version read schema."""

    id: uuid.UUID
    document_id: uuid.UUID
    version: int
    file_size: int
    checksum: str | None = None
    original_filename: str | None = None
    mime_type: str | None = None
    change_note: str | None = None
    uploaded_by_id: uuid.UUID | None = None
    uploaded_by: UserBrief | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SemanticSearchRequest(BaseModel):
    """Payload for semantic search over the vector index."""

    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=50)
    score_threshold: float | None = Field(default=None, ge=-1.0, le=1.0)
    document_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    brand: str | None = None
    doc_type: str | None = None


class SemanticSearchResult(BaseModel):
    """One scored chunk returned by semantic search."""

    chunk_id: uuid.UUID
    document_id: uuid.UUID
    title: str | None = None
    content: str
    score: float
    chunk_index: int
    page: int | None = None
    doc_type: str | None = None
    category_id: uuid.UUID | None = None
    category_name: str | None = None
    brand: str | None = None
    tags: list[str] = []


class SemanticSearchResponse(BaseModel):
    """Semantic search response envelope."""

    query: str
    results: list[SemanticSearchResult]
    total: int
    took_ms: float


class IndexStatsRead(BaseModel):
    """Vector index health/stats for the admin UI."""

    collection: str
    index_status: str
    vector_count: int
    chunk_count: int
    document_count: int
    documents_by_status: dict[str, int]
    embedding_model: str
    embedding_dimension: int


class DocumentChunkRead(BaseModel):
    """Document chunk read schema."""

    id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    content: str
    char_count: int
    word_count: int
    chunk_metadata: dict[str, Any] | None = None

    model_config = {"from_attributes": True}
