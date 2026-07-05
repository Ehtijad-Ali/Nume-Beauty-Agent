"""Embedding pipeline — Phase 2.2.

Turns a document's chunks into vectors in Qdrant, and answers semantic
search queries. Embedding runs as a background job (FastAPI
``BackgroundTasks``) with batch processing and exponential-backoff retry;
job state is persisted on the ``knowledge_documents`` row
(``embedding_status`` / ``embedding_error`` / ``vector_count`` / ...).
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.ai.embeddings import get_embedding_provider
from app.config.settings import get_settings
from app.models.document_chunk import DocumentChunk
from app.models.knowledge_document import KnowledgeDocument
from app.services.vector_store import QdrantVectorStore

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EmbeddingService:
    """Embed document chunks into Qdrant and search them."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.provider = get_embedding_provider()
        self.store = QdrantVectorStore()

    # ------------------------------------------------------------------ #
    # Indexing
    # ------------------------------------------------------------------ #
    def embed_document(self, doc_id: uuid.UUID) -> None:
        """Embed every chunk of one document (batched, with retry)."""
        doc = self.db.get(KnowledgeDocument, doc_id)
        if doc is None:
            logger.warning("Embedding job: document %s no longer exists", doc_id)
            return

        chunks = (
            self.db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == doc_id)
            .order_by(DocumentChunk.chunk_index)
            .all()
        )
        if not chunks:
            doc.embedding_status = "none"
            doc.embedding_error = None
            doc.vector_count = 0
            self.store.delete_document(doc_id)
            self.db.commit()
            return

        doc.embedding_status = "processing"
        doc.embedding_error = None
        self.db.commit()

        try:
            self.store.ensure_collection(self.provider.dimension)
            # Replace any stale vectors from a previous version/index run
            self.store.delete_document(doc_id)

            batch_size = self.settings.embedding_batch_size
            total = 0
            for start in range(0, len(chunks), batch_size):
                batch = chunks[start : start + batch_size]
                vectors = self._embed_with_retry([c.content for c in batch])
                self.store.upsert_chunks(
                    ids=[c.id for c in batch],
                    vectors=vectors,
                    payloads=[self._payload(doc, c) for c in batch],
                )
                total += len(batch)

            doc.embedding_status = "completed"
            doc.embedding_error = None
            doc.embedding_model = self.provider.name
            doc.embedded_at = _utcnow()
            doc.vector_count = total
            self.db.commit()
            logger.info("Embedded document %s: %d vectors", doc_id, total)
        except Exception as exc:
            logger.exception("Embedding job failed for document %s", doc_id)
            # Drop partial vectors so the index never holds a half-embedded doc
            try:
                self.store.delete_document(doc_id)
            except Exception:
                pass
            self.db.rollback()
            doc = self.db.get(KnowledgeDocument, doc_id)
            if doc is not None:
                doc.embedding_status = "failed"
                doc.embedding_error = str(exc)[:2000]
                doc.vector_count = 0
                self.db.commit()

    def _embed_with_retry(self, texts: list[str]) -> list[list[float]]:
        """Embed one batch, retrying with exponential backoff."""
        max_attempts = max(1, self.settings.embedding_max_retries)
        backoff = self.settings.embedding_retry_backoff
        last_error: Exception | None = None
        for attempt in range(max_attempts):
            try:
                return self.provider.embed_texts(texts)
            except Exception as exc:  # provider/IO errors — retry
                last_error = exc
                if attempt < max_attempts - 1:
                    delay = backoff * (2**attempt)
                    logger.warning(
                        "Embedding batch failed (attempt %d/%d): %s — retrying in %.1fs",
                        attempt + 1,
                        max_attempts,
                        exc,
                        delay,
                    )
                    time.sleep(delay)
        raise RuntimeError(
            f"Embedding failed after {max_attempts} attempts: {last_error}"
        ) from last_error

    def _payload(self, doc: KnowledgeDocument, chunk: DocumentChunk) -> dict[str, Any]:
        """Qdrant payload: chunk content + every filterable metadata field."""
        meta = chunk.chunk_metadata or {}
        return {
            "chunk_id": str(chunk.id),
            "document_id": str(doc.id),
            "chunk_index": chunk.chunk_index,
            "content": chunk.content,
            "title": doc.title,
            "doc_type": doc.doc_type,
            "category_id": str(doc.category_id) if doc.category_id else None,
            "category_name": doc.category.name if doc.category else None,
            "brand": doc.brand,
            "tags": [t.strip() for t in doc.tags.split(",") if t.strip()] if doc.tags else [],
            "page": meta.get("page"),
        }

    # ------------------------------------------------------------------ #
    # Search
    # ------------------------------------------------------------------ #
    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        score_threshold: float | None = None,
        document_id: uuid.UUID | None = None,
        category_id: uuid.UUID | None = None,
        brand: str | None = None,
        doc_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Semantic search over the vector index with metadata filters."""
        vector = self.provider.embed_query(query)
        hits = self.store.search(
            vector=vector,
            top_k=top_k,
            score_threshold=score_threshold,
            document_id=document_id,
            category_id=category_id,
            brand=brand,
            doc_type=doc_type,
        )
        results: list[dict[str, Any]] = []
        for hit in hits:
            payload = hit.payload or {}
            results.append(
                {
                    "chunk_id": payload.get("chunk_id"),
                    "document_id": payload.get("document_id"),
                    "title": payload.get("title"),
                    "content": payload.get("content"),
                    "score": round(float(hit.score), 4),
                    "chunk_index": payload.get("chunk_index"),
                    "page": payload.get("page"),
                    "doc_type": payload.get("doc_type"),
                    "category_id": payload.get("category_id"),
                    "category_name": payload.get("category_name"),
                    "brand": payload.get("brand"),
                    "tags": payload.get("tags") or [],
                }
            )
        return results

    # ------------------------------------------------------------------ #
    # Index management
    # ------------------------------------------------------------------ #
    def index_stats(self) -> dict[str, Any]:
        """Vector index + document embedding status summary for the UI."""
        from sqlalchemy import func

        store_stats = self.store.stats()
        status_rows = (
            self.db.query(KnowledgeDocument.embedding_status, func.count(KnowledgeDocument.id))
            .group_by(KnowledgeDocument.embedding_status)
            .all()
        )
        by_status = {status: count for status, count in status_rows}
        chunk_count = self.db.query(func.count(DocumentChunk.id)).scalar() or 0
        return {
            "collection": self.settings.qdrant_collection,
            "index_status": store_stats["status"],
            "vector_count": store_stats["vector_count"],
            "chunk_count": chunk_count,
            "document_count": sum(by_status.values()),
            "documents_by_status": by_status,
            "embedding_model": self.provider.name,
            "embedding_dimension": self.provider.dimension,
        }

    def delete_index(self) -> None:
        """Wipe the vector collection and reset all embedding state."""
        self.store.delete_all(self.provider.dimension)
        self.db.query(KnowledgeDocument).update(
            {
                "embedding_status": "none",
                "embedding_error": None,
                "embedded_at": None,
                "vector_count": 0,
            }
        )
        self.db.commit()

    def delete_document_vectors(self, doc_id: uuid.UUID) -> None:
        """Best-effort removal of one document's vectors."""
        try:
            self.store.delete_document(doc_id)
        except Exception:
            logger.warning("Could not delete vectors for document %s", doc_id, exc_info=True)


def _job_session_factory() -> Session:
    """Create a DB session for a background job (patched in tests)."""
    from app.database.session import SessionLocal

    return SessionLocal()


def run_embedding_job(doc_id: uuid.UUID) -> None:
    """Background-job entrypoint: embed one document in its own DB session.

    Runs after the HTTP response, so it must not reuse the request session —
    and must never raise (a background job failure is recorded on the row).
    """
    db = _job_session_factory()
    try:
        EmbeddingService(db).embed_document(doc_id)
    except Exception:
        logger.exception("Embedding job crashed for document %s", doc_id)
    finally:
        db.close()
