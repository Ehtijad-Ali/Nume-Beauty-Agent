"""
Embedding generators — Phase 2 placeholder.

Will wrap embedding-model clients (OpenAI text-embedding-3, Cohere embed,
local sentence-transformers, etc.) behind a common interface so the RAG
pipeline can be model-agnostic.

Phase 1.1 does NOT implement any embedding generators.
"""


class BaseEmbeddings:
    """Common interface for embedding-model wrappers."""

    name: str = "base"

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts into dense vectors."""
        raise NotImplementedError("Phase 2 — not yet implemented")

    @property
    def dimension(self) -> int:
        """Dimensionality of the vectors produced by this model."""
        raise NotImplementedError("Phase 2 — not yet implemented")
