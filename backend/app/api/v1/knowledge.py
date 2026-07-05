"""Knowledge base endpoints — documents, ingestion, categories, versions, chunks."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_user
from app.dependencies.database import get_db
from app.dependencies.pagination import PaginationDep, pagination_dep
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.knowledge import (
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    DocumentChunkRead,
    DocumentVersionRead,
    IndexStatsRead,
    KnowledgeDocumentCreate,
    KnowledgeDocumentRead,
    KnowledgeDocumentUpdate,
    SemanticSearchRequest,
    SemanticSearchResponse,
)
from app.services.embedding_service import EmbeddingService, run_embedding_job
from app.services.knowledge_service import CategoryService, KnowledgeDocumentService

router = APIRouter()


def _schedule_embedding(background_tasks: BackgroundTasks, doc) -> None:
    """Queue the embedding job for a successfully ingested document."""
    if doc.status == "ready":
        background_tasks.add_task(run_embedding_job, doc.id)


# --------------------------------------------------------------------------- #
# Categories — declared before /{doc_id} so the static path wins.
# --------------------------------------------------------------------------- #
@router.get(
    "/categories",
    response_model=list[CategoryRead],
    summary="List categories",
)
def list_categories(db: Annotated[Session, Depends(get_db)]) -> list[dict]:
    """List all knowledge base categories with document counts."""
    return CategoryService(db).list()


@router.post(
    "/categories",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a category",
)
def create_category(
    payload: CategoryCreate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """Create a knowledge base category."""
    return CategoryService(db).create(payload)


@router.patch(
    "/categories/{category_id}",
    response_model=CategoryRead,
    summary="Update a category",
)
def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """Update a knowledge base category."""
    return CategoryService(db).update(category_id, payload)


@router.delete(
    "/categories/{category_id}",
    response_model=MessageResponse,
    summary="Delete a category",
)
def delete_category(
    category_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """Delete a category. Its documents become uncategorised."""
    CategoryService(db).delete(category_id)
    return {"message": "Category deleted"}


# --------------------------------------------------------------------------- #
# Semantic search + vector index — static paths, declared before /{doc_id}.
# --------------------------------------------------------------------------- #
@router.post(
    "/search",
    response_model=SemanticSearchResponse,
    summary="Semantic search over the knowledge base",
)
def semantic_search(
    payload: SemanticSearchRequest,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """Embed the query and return the most similar chunks (with filters)."""
    import time as _time

    started = _time.perf_counter()
    results = EmbeddingService(db).search(
        payload.query,
        top_k=payload.top_k,
        score_threshold=payload.score_threshold,
        document_id=payload.document_id,
        category_id=payload.category_id,
        brand=payload.brand,
        doc_type=payload.doc_type,
    )
    return {
        "query": payload.query,
        "results": results,
        "total": len(results),
        "took_ms": round((_time.perf_counter() - started) * 1000, 1),
    }


@router.get(
    "/index/stats",
    response_model=IndexStatsRead,
    summary="Vector index statistics",
)
def index_stats(
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Return vector/chunk counts and per-status document totals."""
    return EmbeddingService(db).index_stats()


@router.delete(
    "/index",
    response_model=MessageResponse,
    summary="Delete the vector index",
)
def delete_index(
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """Wipe all vectors and reset every document's embedding status."""
    EmbeddingService(db).delete_index()
    return {"message": "Vector index deleted"}


# --------------------------------------------------------------------------- #
# Documents
# --------------------------------------------------------------------------- #
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
    category_id: uuid.UUID | None = Query(default=None),
    brand: str | None = Query(default=None),
) -> dict:
    """List knowledge documents with filters."""
    service = KnowledgeDocumentService(db)
    items, total = service.list(
        page=pagination.page,
        page_size=pagination.page_size,
        search=pagination.search,
        status=status,
        doc_type=doc_type,
        category_id=category_id,
        brand=brand,
    )
    pages = (total + pagination.page_size - 1) // pagination.page_size if total else 0
    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "pages": pages,
    }


@router.post(
    "/upload",
    response_model=KnowledgeDocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest a document",
)
async def upload_document(
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(get_current_active_user)],
    file: UploadFile = File(..., description="Document to ingest (pdf, docx, txt, md, csv, image)"),
    title: str | None = Form(default=None),
    category_id: uuid.UUID | None = Form(default=None),
    brand: str | None = Form(default=None),
    tags: str | None = Form(default=None, description="Comma-separated tags"),
) -> dict:
    """Upload a file, store it, and run the ingestion pipeline.

    The response reflects the ingestion outcome: ``ready`` on success or
    ``failed`` (with ``error_message``) if the file could not be parsed.
    Embedding runs as a background job afterwards (``embedding_status``).
    """
    service = KnowledgeDocumentService(db)
    content = await file.read()
    doc = service.upload_document(
        filename=file.filename or "untitled",
        content=content,
        mime_type=file.content_type or "application/octet-stream",
        title=title,
        category_id=category_id,
        brand=brand,
        tags=tags,
        actor_id=actor.id,
    )
    _schedule_embedding(background_tasks, doc)
    return doc


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
    """Update a knowledge document's metadata."""
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
    """Delete a knowledge document, its chunks, versions and stored files."""
    KnowledgeDocumentService(db).delete(doc_id)
    return {"message": "Document deleted"}


@router.post(
    "/{doc_id}/replace",
    response_model=KnowledgeDocumentRead,
    summary="Replace a document's file",
)
async def replace_document(
    doc_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(get_current_active_user)],
    file: UploadFile = File(..., description="New file for this document"),
    change_note: str | None = Form(default=None),
) -> dict:
    """Upload a new file for an existing document (creates a new version)."""
    service = KnowledgeDocumentService(db)
    content = await file.read()
    doc = service.replace_document(
        doc_id,
        filename=file.filename or "untitled",
        content=content,
        mime_type=file.content_type or "application/octet-stream",
        change_note=change_note,
        actor_id=actor.id,
    )
    _schedule_embedding(background_tasks, doc)
    return doc


@router.post(
    "/{doc_id}/reindex",
    response_model=KnowledgeDocumentRead,
    summary="Re-index a document",
)
def reindex_document(
    doc_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """Re-run ingestion on the stored file, then re-embed in the background."""
    doc = KnowledgeDocumentService(db).reindex_document(doc_id)
    _schedule_embedding(background_tasks, doc)
    return doc


@router.get(
    "/{doc_id}/chunks",
    response_model=PaginatedResponse[DocumentChunkRead],
    summary="List a document's chunks",
)
def list_document_chunks(
    doc_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
) -> dict:
    """Return the text chunks extracted from a document."""
    items, total = KnowledgeDocumentService(db).list_chunks(
        doc_id, page=page, page_size=page_size
    )
    pages = (total + page_size - 1) // page_size if total else 0
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }


@router.get(
    "/{doc_id}/versions",
    response_model=list[DocumentVersionRead],
    summary="List a document's versions",
)
def list_document_versions(
    doc_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> list:
    """Return the version history of a document (newest first)."""
    return KnowledgeDocumentService(db).list_versions(doc_id)


@router.get(
    "/{doc_id}/download",
    summary="Download a document's current file",
)
def download_document(
    doc_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
) -> FileResponse:
    """Stream the current stored file of a document."""
    service = KnowledgeDocumentService(db)
    doc = service.get(doc_id)
    path = service.get_file_path(doc_id)
    return FileResponse(
        path=path,
        media_type=doc.mime_type or "application/octet-stream",
        filename=doc.original_filename or doc.title,
    )
