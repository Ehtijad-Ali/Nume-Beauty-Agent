"""Category repository."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select

from app.models.category import Category
from app.models.knowledge_document import KnowledgeDocument
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    """Repository for :class:`Category`."""

    model = Category

    def get_by_slug(self, slug: str) -> Category | None:
        stmt = select(Category).where(Category.slug == slug)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_name(self, name: str) -> Category | None:
        stmt = select(Category).where(func.lower(Category.name) == name.lower())
        return self.db.execute(stmt).scalar_one_or_none()

    def list_all(self) -> list[Category]:
        stmt = select(Category).order_by(Category.name.asc())
        return list(self.db.execute(stmt).scalars().all())

    def document_counts(self) -> dict[uuid.UUID, int]:
        """Return a mapping of category_id -> number of documents."""
        stmt = (
            select(KnowledgeDocument.category_id, func.count(KnowledgeDocument.id))
            .where(KnowledgeDocument.category_id.is_not(None))
            .group_by(KnowledgeDocument.category_id)
        )
        return {row[0]: row[1] for row in self.db.execute(stmt).all()}
