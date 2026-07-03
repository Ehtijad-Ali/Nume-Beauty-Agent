"""Upload model — file uploads (assets, reports, etc.)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    pass


class Upload(Base, UUIDPKMixin, TimestampMixin):
    """A file upload record."""

    __tablename__ = "uploads"

    filename: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)
    size: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    storage_type: Mapped[str] = mapped_column(String(20), default="local", nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="other", nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="completed", nullable=False, index=True)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    uploaded_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Upload {self.filename}>"
