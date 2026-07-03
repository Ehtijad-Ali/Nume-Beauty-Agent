"""
Agent memory — Phase 2 placeholder.

Will provide short-term (per-conversation) and long-term (cross-session)
memory stores for AI agents. Likely backed by Redis (short-term) and
PostgreSQL / vector store (long-term).

Phase 1.1 does NOT implement any memory stores.
"""


class BaseMemory:
    """Common interface for agent memory stores."""

    async def add(self, key: str, value: str, **metadata) -> None:
        """Add an entry to memory."""
        raise NotImplementedError("Phase 2 — not yet implemented")

    async def get(self, key: str) -> str | None:
        """Retrieve an entry by key."""
        raise NotImplementedError("Phase 2 — not yet implemented")

    async def search(self, query: str, *, top_k: int = 5) -> list:
        """Semantic search over memory entries."""
        raise NotImplementedError("Phase 2 — not yet implemented")
