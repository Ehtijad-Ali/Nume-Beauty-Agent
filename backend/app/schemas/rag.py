"""RAG engine schemas — Phase 2.3."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------- #
# Query
# --------------------------------------------------------------------------- #


class RagQueryRequest(BaseModel):
    """One RAG turn: a user question plus optional retrieval controls."""

    message: str = Field(min_length=1, max_length=4000)
    conversation_id: uuid.UUID | None = None
    top_k: int | None = Field(default=None, ge=1, le=20)
    score_threshold: float | None = Field(default=None, ge=-1.0, le=1.0)
    # Metadata filters (passed to the vector store)
    document_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    brand: str | None = None
    doc_type: str | None = None
    # Override the server-side grounding default for this turn
    allow_general_knowledge: bool | None = None


class RetrievedChunkRead(BaseModel):
    """A scored chunk as used by the engine (admin: 'view retrieved chunks')."""

    chunk_id: uuid.UUID
    document_id: uuid.UUID
    title: str | None = None
    content: str
    score: float
    rank_score: float | None = None
    priority: bool = False
    citation: int | None = None
    chunk_index: int
    page: int | None = None
    doc_type: str | None = None
    category_id: uuid.UUID | None = None
    category_name: str | None = None
    brand: str | None = None
    tags: list[str] = []


class RagSourceRead(BaseModel):
    """A cited source document."""

    document_id: uuid.UUID
    title: str | None = None
    doc_type: str | None = None
    category_name: str | None = None
    brand: str | None = None
    citations: list[int] = []
    chunks_used: int = 0
    best_score: float = 0.0


class RagUsage(BaseModel):
    input_tokens: int
    output_tokens: int
    total_tokens: int


class RagTimings(BaseModel):
    retrieval_ms: float
    llm_ms: float
    total_ms: float


class FinalPrompt(BaseModel):
    """The exact prompt sent to the LLM (admin prompt debugger)."""

    system: str
    messages: list[dict[str, Any]]


class RagQueryResponse(BaseModel):
    """Full RAG response envelope: answer + context + debug payload."""

    conversation_id: uuid.UUID
    message_id: uuid.UUID
    answer: str
    sources: list[RagSourceRead]
    retrieved_chunks: list[RetrievedChunkRead]
    final_prompt: FinalPrompt
    provider: str
    model: str | None = None
    usage: RagUsage
    timings: RagTimings


# --------------------------------------------------------------------------- #
# Conversations & messages
# --------------------------------------------------------------------------- #


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=500)


class ConversationRead(BaseModel):
    id: uuid.UUID
    title: str
    message_count: int
    total_input_tokens: int
    total_output_tokens: int
    last_message_at: datetime | None = None
    user_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RagMessageRead(BaseModel):
    """A conversation turn (without heavy debug payloads)."""

    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    provider: str | None = None
    model: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    retrieval_ms: float | None = None
    llm_ms: float | None = None
    total_ms: float | None = None
    sources: list[RagSourceRead] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RagMessageDebugRead(RagMessageRead):
    """Full admin debug view of an assistant turn."""

    retrieved_chunks: list[RetrievedChunkRead] | None = None
    final_prompt: FinalPrompt | None = None
    rag_metadata: dict[str, Any] | None = None


# --------------------------------------------------------------------------- #
# Admin
# --------------------------------------------------------------------------- #


class RagModelUsage(BaseModel):
    provider: str
    model: str | None = None
    queries: int
    input_tokens: int
    output_tokens: int


class RagStatsRead(BaseModel):
    """Token usage + latency summary for the admin panel."""

    conversation_count: int
    query_count: int
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    avg_total_ms: float | None = None
    avg_retrieval_ms: float | None = None
    avg_llm_ms: float | None = None
    by_model: list[RagModelUsage] = []


class RagConfigRead(BaseModel):
    """Active RAG/LLM configuration (no secrets)."""

    llm_provider: str
    llm_model: str
    llm_configured: bool
    embedding_model: str
    top_k: int
    score_threshold: float
    max_context_chars: int
    max_chunks_per_document: int
    history_messages: int
    allow_general_knowledge: bool
