"""Retriever — Phase 2.3.

Semantic retrieval layer of the RAG engine. Wraps the Phase 2.2 vector
search and adds:

  * multi-document retrieval — caps chunks per document so a single long
    document cannot crowd out the rest of the knowledge base;
  * context ranking — blends vector similarity with a priority boost for
    the brand-critical categories (brand guidelines, brand voice, product
    catalogue, customer personas);
  * metadata filtering — passes document/category/brand/doc_type filters
    straight through to Qdrant.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.services.embedding_service import EmbeddingService

# Categories/tags/titles the system prompt says to prioritise. Matching is
# substring-based over lowercase text so "Brand Guidelines", "brand-voice"
# and "Product Catalog" all hit.
PRIORITY_TERMS = (
    "brand guideline",
    "brand voice",
    "product catalog",  # also matches "product catalogue"
    "customer persona",
)


def priority_boost(chunk: dict[str, Any]) -> bool:
    """Whether a retrieved chunk belongs to a priority knowledge source."""
    haystack = " ".join(
        str(value).lower()
        for value in (
            chunk.get("category_name"),
            chunk.get("title"),
            " ".join(chunk.get("tags") or []),
        )
        if value
    )
    return any(term in haystack for term in PRIORITY_TERMS)


class Retriever:
    """Retrieve, rank and diversify knowledge chunks for a query."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.search_service = EmbeddingService(db)

    def retrieve(
        self,
        query: str,
        *,
        top_k: int | None = None,
        score_threshold: float | None = None,
        document_id: uuid.UUID | None = None,
        category_id: uuid.UUID | None = None,
        brand: str | None = None,
        doc_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return the ``top_k`` best chunks, ranked and document-diversified.

        Each chunk dict is the Phase 2.2 search result plus ``priority`` and
        ``rank_score`` fields explaining the final ordering.
        """
        top_k = top_k or self.settings.rag_top_k
        if score_threshold is None:
            score_threshold = self.settings.rag_score_threshold

        # Over-fetch so re-ranking and per-document caps have room to work.
        candidates = self.search_service.search(
            query,
            top_k=max(top_k * 3, top_k),
            score_threshold=score_threshold,
            document_id=document_id,
            category_id=category_id,
            brand=brand,
            doc_type=doc_type,
        )

        boost = self.settings.rag_priority_boost
        for chunk in candidates:
            chunk["priority"] = priority_boost(chunk)
            chunk["rank_score"] = round(
                chunk["score"] + (boost if chunk["priority"] else 0.0), 4
            )
        candidates.sort(key=lambda c: c["rank_score"], reverse=True)

        # Multi-document retrieval: cap chunks per document (unless the
        # caller explicitly filtered to a single document).
        per_doc_cap = self.settings.rag_max_chunks_per_document
        selected: list[dict[str, Any]] = []
        per_doc: dict[str, int] = {}
        for chunk in candidates:
            doc = str(chunk.get("document_id"))
            if document_id is None and per_doc.get(doc, 0) >= per_doc_cap:
                continue
            per_doc[doc] = per_doc.get(doc, 0) + 1
            selected.append(chunk)
            if len(selected) >= top_k:
                break
        return selected
