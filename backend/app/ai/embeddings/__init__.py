"""
Embedding generators.

Phase 2.2 implements local embeddings via ``fastembed`` plus a deterministic
hashing fallback, behind the :class:`EmbeddingProvider` interface in
:mod:`app.ai.embeddings.providers`.
"""

from app.ai.embeddings.providers import (
    EmbeddingProvider,
    FastEmbedProvider,
    HashingProvider,
    get_embedding_provider,
)

__all__ = [
    "EmbeddingProvider",
    "FastEmbedProvider",
    "HashingProvider",
    "get_embedding_provider",
]
