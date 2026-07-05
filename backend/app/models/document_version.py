"""DocumentVersion model — immutable history of a knowledge document's files."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.knowledge_document import KnowledgeDocument
    from app.models.user import User


class DocumentVersion(Base, UUIDPKMixin, TimestampMixin):
    """A stored version of a knowledge document's underlying file."""

    __tablename__ = "document_versions"
    __table_args__ = (
        UniqueConstraint("document_id", "version", name="uq_document_versions_doc_ver"),
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    file_size: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    original_filename: Mapped[str | None] = mapped_column(String(500), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    change_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    uploaded_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    document: Mapped["KnowledgeDocument"] = relationship(back_populates="versions")
    uploaded_by: Mapped["User | None"] = relationship(lazy="joined")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DocumentVersion {self.document_id} v{self.version}>"
