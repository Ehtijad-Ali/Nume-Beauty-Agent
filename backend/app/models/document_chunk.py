"""DocumentChunk model — cleaned text segments extracted from a document."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Integer, Text, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.knowledge_document import KnowledgeDocument

# JSONB on PostgreSQL, plain JSON on SQLite (for tests).
_meta_type = JSONB().with_variant(JSON(), "sqlite")


class DocumentChunk(Base, UUIDPKMixin, TimestampMixin):
    """An ordered chunk of normalised text belonging to a knowledge document.

    Chunks are the unit later phases will embed/index; Phase 2.1 only creates
    and stores them (no embeddings, no vector store).
    """

    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_document_chunks_doc_idx"),
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    char_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Source location hints (page number, row range, section title, ...)
    chunk_metadata: Mapped[dict[str, Any] | None] = mapped_column(_meta_type, nullable=True)

    document: Mapped["KnowledgeDocument"] = relationship(back_populates="chunks")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DocumentChunk {self.document_id}#{self.chunk_index}>"
