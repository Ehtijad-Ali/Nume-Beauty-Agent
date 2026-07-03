"""KnowledgeDocument model — indexed reference material."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, String, Text
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    pass


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

    uploaded_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<KnowledgeDocument {self.title}>"
