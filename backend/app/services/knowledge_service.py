"""Knowledge document service."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.knowledge_document import KnowledgeDocument
from app.repositories.knowledge_repo import KnowledgeDocumentRepository
from app.schemas.knowledge import KnowledgeDocumentCreate, KnowledgeDocumentUpdate


class KnowledgeDocumentService:
    """Business logic for knowledge documents."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = KnowledgeDocumentRepository(db)

    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        status: str | None = None,
        doc_type: str | None = None,
    ) -> tuple[list[KnowledgeDocument], int]:
        """List documents with filters."""
        filters: dict[str, Any] = {}
        if status:
            filters["status"] = status
        if doc_type:
            filters["doc_type"] = doc_type
        return self.repo.list(
            offset=(page - 1) * page_size,
            limit=page_size,
            filters=filters,
            search=search,
        )

    def get(self, doc_id: uuid.UUID) -> KnowledgeDocument:
        """Return a document by ID or raise."""
        doc = self.repo.get(doc_id)
        if not doc:
            raise NotFoundError("Knowledge document not found")
        return doc

    def create(
        self,
        payload: KnowledgeDocumentCreate,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> KnowledgeDocument:
        """Create a knowledge document record."""
        data = payload.model_dump()
        if actor_id:
            data["uploaded_by_id"] = actor_id
        doc = self.repo.create(data)
        self.db.commit()
        return doc

    def update(self, doc_id: uuid.UUID, payload: KnowledgeDocumentUpdate) -> KnowledgeDocument:
        """Update a knowledge document."""
        doc = self.get(doc_id)
        data = payload.model_dump(exclude_unset=True)
        updated = self.repo.update(doc, data)
        self.db.commit()
        return updated

    def delete(self, doc_id: uuid.UUID) -> None:
        """Delete a knowledge document."""
        doc = self.get(doc_id)
        self.repo.delete(doc)
        self.db.commit()
