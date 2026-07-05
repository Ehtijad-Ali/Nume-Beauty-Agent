"""Qdrant vector store wrapper — Phase 2.2.

Wraps the ``qdrant-client`` behind the small surface the knowledge base
needs: ensure the collection exists, upsert chunk vectors with metadata,
filtered similarity search, and per-document / whole-index deletion.

Deployment modes (``qdrant_mode`` setting):
  * ``embedded`` — persists to ``qdrant_path`` on disk, no server needed.
    Single-process only; multi-worker deployments must use ``remote``.
  * ``remote``   — connects to ``qdrant_url`` (optionally ``qdrant_api_key``).
  * ``memory``   — throwaway in-process store, used by the test suite.
"""

from __future__ import annotations

import logging
import uuid
from functools import lru_cache
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client import models as qm

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_client() -> QdrantClient:
    """Return the process-wide Qdrant client (embedded mode requires this)."""
    settings = get_settings()
    if settings.qdrant_mode == "memory":
        return QdrantClient(":memory:")
    if settings.qdrant_mode == "remote":
        return QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
        )
    return QdrantClient(path=settings.qdrant_path)


def reset_client_cache() -> None:
    """Drop the cached client (test isolation helper)."""
    _get_client.cache_clear()


class QdrantVectorStore:
    """Thin, typed wrapper around the Qdrant collection for chunk vectors."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = _get_client()
        self.collection = self.settings.qdrant_collection

    # ------------------------------------------------------------------ #
    # Collection lifecycle
    # ------------------------------------------------------------------ #
    def ensure_collection(self, dim: int) -> None:
        """Create the collection (and payload indexes) if it doesn't exist."""
        if self.client.collection_exists(self.collection):
            return
        self.client.create_collection(
            collection_name=self.collection,
            vectors_config=qm.VectorParams(size=dim, distance=qm.Distance.COSINE),
        )
        for field in ("document_id", "category_id", "brand", "doc_type"):
            self.client.create_payload_index(
                collection_name=self.collection,
                field_name=field,
                field_schema=qm.PayloadSchemaType.KEYWORD,
            )
        logger.info("Created Qdrant collection '%s' (dim=%d)", self.collection, dim)

    def delete_all(self, dim: int | None = None) -> None:
        """Drop every vector. Recreates an empty collection when dim given."""
        if self.client.collection_exists(self.collection):
            self.client.delete_collection(self.collection)
        if dim is not None:
            self.ensure_collection(dim)

    # ------------------------------------------------------------------ #
    # Writes
    # ------------------------------------------------------------------ #
    def upsert_chunks(
        self,
        *,
        vectors: list[list[float]],
        payloads: list[dict[str, Any]],
        ids: list[uuid.UUID],
    ) -> None:
        """Upsert chunk vectors; the point id is the chunk's UUID."""
        if not vectors:
            return
        self.client.upsert(
            collection_name=self.collection,
            points=[
                qm.PointStruct(id=str(id_), vector=vector, payload=payload)
                for id_, vector, payload in zip(ids, vectors, payloads)
            ],
        )

    def delete_document(self, document_id: uuid.UUID) -> None:
        """Remove every vector belonging to one document."""
        if not self.client.collection_exists(self.collection):
            return
        self.client.delete(
            collection_name=self.collection,
            points_selector=qm.FilterSelector(
                filter=qm.Filter(
                    must=[
                        qm.FieldCondition(
                            key="document_id", match=qm.MatchValue(value=str(document_id))
                        )
                    ]
                )
            ),
        )

    # ------------------------------------------------------------------ #
    # Reads
    # ------------------------------------------------------------------ #
    def search(
        self,
        *,
        vector: list[float],
        top_k: int = 5,
        score_threshold: float | None = None,
        document_id: uuid.UUID | None = None,
        category_id: uuid.UUID | None = None,
        brand: str | None = None,
        doc_type: str | None = None,
    ) -> list[qm.ScoredPoint]:
        """Similarity search with optional metadata filters."""
        if not self.client.collection_exists(self.collection):
            return []
        conditions: list[qm.FieldCondition] = []
        if document_id:
            conditions.append(
                qm.FieldCondition(key="document_id", match=qm.MatchValue(value=str(document_id)))
            )
        if category_id:
            conditions.append(
                qm.FieldCondition(key="category_id", match=qm.MatchValue(value=str(category_id)))
            )
        if brand:
            conditions.append(qm.FieldCondition(key="brand", match=qm.MatchValue(value=brand)))
        if doc_type:
            conditions.append(
                qm.FieldCondition(key="doc_type", match=qm.MatchValue(value=doc_type))
            )
        return self.client.search(
            collection_name=self.collection,
            query_vector=vector,
            limit=top_k,
            query_filter=qm.Filter(must=conditions) if conditions else None,
            score_threshold=score_threshold,
            with_payload=True,
        )

    def count(self, document_id: uuid.UUID | None = None) -> int:
        """Number of vectors in the collection (optionally for one document)."""
        if not self.client.collection_exists(self.collection):
            return 0
        count_filter = None
        if document_id:
            count_filter = qm.Filter(
                must=[
                    qm.FieldCondition(
                        key="document_id", match=qm.MatchValue(value=str(document_id))
                    )
                ]
            )
        return self.client.count(
            collection_name=self.collection, count_filter=count_filter, exact=True
        ).count

    def stats(self) -> dict[str, Any]:
        """Collection status summary for the admin UI."""
        if not self.client.collection_exists(self.collection):
            return {"exists": False, "status": "not_created", "vector_count": 0}
        info = self.client.get_collection(self.collection)
        return {
            "exists": True,
            "status": str(getattr(info, "status", "green")).split(".")[-1].lower(),
            "vector_count": self.count(),
        }
