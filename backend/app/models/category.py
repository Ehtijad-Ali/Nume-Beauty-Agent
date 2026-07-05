"""Category model — knowledge base document categories."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.knowledge_document import KnowledgeDocument


class Category(Base, UUIDPKMixin, TimestampMixin):
    """A category used to organise knowledge base documents."""

    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)  # hex color for UI badges

    # On delete, the ORM nulls out category_id on documents (works on SQLite
    # tests too, where FK ON DELETE SET NULL is not enforced by default).
    documents: Mapped[list["KnowledgeDocument"]] = relationship(back_populates="category")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Category {self.name}>"
