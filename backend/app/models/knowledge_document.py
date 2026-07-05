"""KnowledgeDocument model — indexed reference material."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.document_chunk import DocumentChunk
    from app.models.document_version import DocumentVersion
    from app.models.user import User

# JSONB on PostgreSQL, plain JSON on SQLite (for tests).
_meta_type = JSONB().with_variant(JSON(), "sqlite")


class KnowledgeDocument(Base, UUIDPKMixin, TimestampMixin):
    """A document stored in the knowledge base."""

    __tablename__ = "knowledge_documents"

    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    doc_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # pdf, docx, xlsx...
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    file_size: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="queued", nullable=False, index=True)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)  # comma-separated
    excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Phase 2.1: ingestion metadata ---
    original_filename: Mapped[str | None] = mapped_column(String(500), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    language: Mapped[str | None] = mapped_column(String(20), nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    doc_metadata: Mapped[dict[str, Any] | None] = mapped_column(_meta_type, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # --- Phase 2.2: vector index state ---
    # none | pending | processing | completed | failed
    embedding_status: Mapped[str] = mapped_column(
        String(20), default="none", nullable=False, index=True
    )
    embedding_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(200), nullable=True)
    embedded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    vector_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    category_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    uploaded_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    category: Mapped["Category | None"] = relationship(back_populates="documents", lazy="joined")
    uploaded_by: Mapped["User | None"] = relationship(lazy="joined")
    # ORM-level cascade (not passive) so deletes also work on SQLite tests,
    # where FK ON DELETE CASCADE is not enforced by default.
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentChunk.chunk_index",
    )
    versions: Mapped[list["DocumentVersion"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentVersion.version.desc()",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<KnowledgeDocument {self.title}>"
