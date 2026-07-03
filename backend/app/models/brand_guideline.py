"""BrandGuideline model — brand voice, palette and tone rules."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    pass


class BrandGuideline(Base, UUIDPKMixin, TimestampMixin):
    """Brand guideline document (voice, tone, palette, do/don'ts)."""

    __tablename__ = "brand_guidelines"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    guideline_type: Mapped[str] = mapped_column(String(50), nullable=False)  # voice, palette, tone...
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<BrandGuideline {self.name}>"
