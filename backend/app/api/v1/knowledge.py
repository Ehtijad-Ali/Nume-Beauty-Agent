"""Knowledge documents CRUD endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_user
from app.dependencies.database import get_db
from app.dependencies.pagination import PaginationDep, pagination_dep
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.knowledge import (
    KnowledgeDocumentCreate,
    KnowledgeDocumentRead,
    KnowledgeDocumentUpdate,
)
from app.services.knowledge_service import KnowledgeDocumentService

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[KnowledgeDocumentRead],
    summary="List knowledge documents",
)
def list_documents(
    db: Annotated[Session, Depends(get_db)],
    pagination: Annotated[PaginationDep, Depends(pagination_dep)],
    status: str | None = Query(
        default=None, pattern="^(queued|processing|ready|failed)$"
    ),
    doc_type: str | None = Query(default=None),
) -> dict:
    """List knowledge documents with filters."""
    service = KnowledgeDocumentService(db)
    items, total = service.list(
        page=pagination.page,
        page_size=pagination.page_size,
        search=pagination.search,
        status=status,
        doc_type=doc_type,
    )
    pages = (total + pagination.page_size - 1) // pagination.page_size if total else 0
    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "pages": pages,
    }


@router.get(
    "/{doc_id}",
    response_model=KnowledgeDocumentRead,
    summary="Get a document",
)
def get_document(
    doc_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Return a knowledge document by ID."""
    return KnowledgeDocumentService(db).get(doc_id)


@router.post(
    "",
    response_model=KnowledgeDocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a document record",
)
def create_document(
    payload: KnowledgeDocumentCreate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """Create a knowledge document record (does not store file content)."""
    return KnowledgeDocumentService(db).create(payload, actor_id=actor.id)


@router.patch(
    "/{doc_id}",
    response_model=KnowledgeDocumentRead,
    summary="Update a document",
)
def update_document(
    doc_id: uuid.UUID,
    payload: KnowledgeDocumentUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Update a knowledge document."""
    return KnowledgeDocumentService(db).update(doc_id, payload)


@router.delete(
    "/{doc_id}",
    response_model=MessageResponse,
    summary="Delete a document",
)
def delete_document(
    doc_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Delete a knowledge document."""
    KnowledgeDocumentService(db).delete(doc_id)
    return {"message": "Document deleted"}
