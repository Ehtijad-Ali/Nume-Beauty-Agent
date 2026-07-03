"""
RAG (Retrieval-Augmented Generation) pipeline — Phase 2 placeholder.

Will orchestrate:
  1. Document ingestion → chunking → embedding → vector store upsert
  2. Query embedding → vector search → re-rank → context assembly
  3. LLM completion with retrieved context + citations

The RAG pipeline composes components from `app.ai.embeddings`,
`app.ai.providers`, `app.ai.prompts` and `app.vector`.

Phase 1.1 does NOT implement any RAG functionality. Knowledge documents
uploaded via `/api/v1/uploads` and registered via `/api/v1/knowledge` are
stored in PostgreSQL only; they are NOT yet indexed in any vector store.
"""


class RAGPipeline:
    """End-to-end RAG pipeline (Phase 2 placeholder)."""

    async def ingest(self, document_id: str) -> None:
        """Chunk, embed and index a document into the vector store."""
        raise NotImplementedError("Phase 2 — not yet implemented")

    async def query(self, question: str, *, top_k: int = 5) -> dict:
        """Retrieve relevant chunks and generate an answer with citations."""
        raise NotImplementedError("Phase 2 — not yet implemented")
