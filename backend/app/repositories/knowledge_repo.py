"""Knowledge document, chunk and version repositories."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import delete, func, select

from app.models.document_chunk import DocumentChunk
from app.models.document_version import DocumentVersion
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
            search_fields=search_fields or ["title", "tags", "excerpt", "brand", "original_filename"],
            order_by=order_by,
            order_dir=order_dir,
        )


class DocumentChunkRepository(BaseRepository[DocumentChunk]):
    """Repository for :class:`DocumentChunk`."""

    model = DocumentChunk

    def list_for_document(
        self, document_id: uuid.UUID, *, offset: int = 0, limit: int = 50
    ) -> tuple[list[DocumentChunk], int]:
        base = select(DocumentChunk).where(DocumentChunk.document_id == document_id)
        total = self.db.execute(
            select(func.count()).select_from(base.subquery())
        ).scalar_one()
        stmt = base.order_by(DocumentChunk.chunk_index.asc()).offset(offset).limit(limit)
        return list(self.db.execute(stmt).scalars().all()), total

    def delete_for_document(self, document_id: uuid.UUID) -> int:
        """Delete all chunks of a document. Returns the number removed."""
        result = self.db.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )
        return result.rowcount or 0


class DocumentVersionRepository(BaseRepository[DocumentVersion]):
    """Repository for :class:`DocumentVersion`."""

    model = DocumentVersion

    def list_for_document(self, document_id: uuid.UUID) -> list[DocumentVersion]:
        stmt = (
            select(DocumentVersion)
            .where(DocumentVersion.document_id == document_id)
            .order_by(DocumentVersion.version.desc())
        )
        return list(self.db.execute(stmt).scalars().all())
