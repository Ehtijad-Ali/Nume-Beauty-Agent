"""Embedding providers — Phase 2.2.

Pluggable, synchronous embedding backends behind a small interface so the
indexing/search pipeline stays model-agnostic:

* :class:`FastEmbedProvider` — local ONNX inference via ``fastembed``
  (default: ``BAAI/bge-small-en-v1.5``, 384 dimensions). The model is
  downloaded once on first use and cached by fastembed.
* :class:`HashingProvider` — deterministic character-ngram hashing vectors.
  No dependencies, instant, stable across runs. Used by the test suite and
  as a last-resort fallback when fastembed is not installed. Not semantic —
  similarity only reflects shared surface tokens.
"""

from __future__ import annotations

import hashlib
import logging
import math
import re
import threading
from functools import lru_cache
from typing import Protocol, runtime_checkable

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Interface every embedding backend implements."""

    name: str

    @property
    def dimension(self) -> int:
        """Dimensionality of produced vectors."""
        ...

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of passages/documents."""
        ...

    def embed_query(self, text: str) -> list[float]:
        """Embed a search query."""
        ...


class FastEmbedProvider:
    """Local ONNX embeddings via the ``fastembed`` package."""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5") -> None:
        self.name = f"fastembed:{model_name}"
        self.model_name = model_name
        self._model = None
        self._lock = threading.Lock()

    def _get_model(self):
        # Lazy + locked: the first call downloads/loads the ONNX model.
        if self._model is None:
            with self._lock:
                if self._model is None:
                    from fastembed import TextEmbedding

                    logger.info("Loading fastembed model %s ...", self.model_name)
                    self._model = TextEmbedding(model_name=self.model_name)
        return self._model

    @property
    def dimension(self) -> int:
        from fastembed import TextEmbedding

        for desc in TextEmbedding.list_supported_models():
            if desc["model"] == self.model_name:
                return int(desc["dim"])
        # Fall back to probing the model itself
        return len(next(iter(self._get_model().embed(["probe"]))))

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        model = self._get_model()
        return [vector.tolist() for vector in model.embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        model = self._get_model()
        return next(iter(model.query_embed(text))).tolist()


class HashingProvider:
    """Deterministic bag-of-ngrams hashing embeddings (tests/fallback only)."""

    name = "hashing"

    def __init__(self, dim: int = 384) -> None:
        self._dim = dim

    @property
    def dimension(self) -> int:
        return self._dim

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self._dim
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        for token in tokens:
            # Word hash plus character trigrams for a little fuzziness
            grams = [token] + [token[i : i + 3] for i in range(max(len(token) - 2, 1))]
            for gram in grams:
                digest = hashlib.md5(gram.encode("utf-8")).digest()
                index = int.from_bytes(digest[:4], "little") % self._dim
                sign = 1.0 if digest[4] % 2 == 0 else -1.0
                vector[index] += sign
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed_one(text)


@lru_cache(maxsize=1)
def get_embedding_provider() -> EmbeddingProvider:
    """Return the configured embedding provider (cached singleton)."""
    settings = get_settings()
    if settings.embedding_provider == "hashing":
        return HashingProvider()
    try:
        import fastembed  # noqa: F401  — verify the optional dep exists

        return FastEmbedProvider(settings.embedding_model)
    except ImportError:
        logger.warning(
            "fastembed is not installed — falling back to the non-semantic "
            "hashing provider. Install fastembed for real semantic search."
        )
        return HashingProvider()
