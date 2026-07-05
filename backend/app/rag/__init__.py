"""RAG (Retrieval-Augmented Generation) engine — Phase 2.3.

Pipeline: user prompt → semantic search (:mod:`app.rag.retriever`)
→ context assembly (:mod:`app.rag.context_builder`) → prompt building with
brand context and conversation memory (:mod:`app.rag.prompt_builder`)
→ LLM completion (:mod:`app.ai.providers`) → cited answer with full debug
payload (:mod:`app.rag.engine`).
"""

from app.rag.engine import RAGEngine
from app.rag.retriever import Retriever

__all__ = ["RAGEngine", "Retriever"]
