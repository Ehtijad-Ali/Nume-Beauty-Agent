"""
Vector store interface — Phase 2 placeholder.

Defines a backend-agnostic interface for vector databases so the RAG
pipeline can target pgvector, Pinecone, Weaviate, Qdrant or Chroma without
the rest of the codebase caring about the underlying engine.

Phase 1.1 does NOT include a vector database. PostgreSQL (already part of
the stack) is the most likely candidate — `pgvector` extension can be added
in a single migration when Phase 2 lands.
"""

from __future__ import annotations

from typing import Any


class VectorStore:
    """Backend-agnostic vector store interface (Phase 2 placeholder)."""

    async def upsert(self, *, id: str, vector: list[float], metadata: dict[str, Any] | None = None) -> None:
        """Insert or update a vector."""
        raise NotImplementedError("Phase 2 — not yet implemented")

    async def search(self, *, query: list[float], top_k: int = 5, filter: dict | None = None) -> list[dict]:
        """Return the top-k nearest neighbours for the query vector."""
        raise NotImplementedError("Phase 2 — not yet implemented")

    async def delete(self, id: str) -> None:
        """Delete a vector by id."""
        raise NotImplementedError("Phase 2 — not yet implemented")
