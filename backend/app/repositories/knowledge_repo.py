"""Knowledge document repository."""

from __future__ import annotations

from typing import Any

from app.models.knowledge_document import KnowledgeDocument
from app.repositories.base import BaseRepository


class KnowledgeDocumentRepository(BaseRepository[KnowledgeDocument]):
    """Repository for :class:`KnowledgeDocument`."""

    model = KnowledgeDocument

    def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        filters: dict[str, Any] | None = None,
        search: str | None = None,
        search_fields: list[str] | None = None,
        order_by: str | None = None,
        order_dir: str = "asc",
    ) -> tuple[list[KnowledgeDocument], int]:
        return super().list(
            offset=offset,
            limit=limit,
            filters=filters,
            search=search,
            search_fields=search_fields or ["title", "tags", "excerpt"],
            order_by=order_by,
            order_dir=order_dir,
        )
