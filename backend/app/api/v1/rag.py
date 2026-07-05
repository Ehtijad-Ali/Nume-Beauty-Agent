"""RAG engine endpoints — query, conversations, admin debug/stats."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.dependencies.auth import get_current_active_user
from app.dependencies.database import get_db
from app.dependencies.pagination import PaginationDep, pagination_dep
from app.models.user import User
from app.rag.engine import RAGEngine
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.rag import (
    ConversationCreate,
    ConversationRead,
    RagConfigRead,
    RagMessageDebugRead,
    RagMessageRead,
    RagQueryRequest,
    RagQueryResponse,
    RagStatsRead,
)

router = APIRouter()


# --------------------------------------------------------------------------- #
# Query
# --------------------------------------------------------------------------- #
@router.post(
    "/query",
    response_model=RagQueryResponse,
    summary="Ask the knowledge base (RAG)",
)
def rag_query(
    payload: RagQueryRequest,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """Run one retrieval-augmented turn.

    The response includes the answer plus the full debug envelope:
    retrieved context, final prompt, source documents, similarity scores,
    token usage and response times.
    """
    return RAGEngine(db).query(
        payload.message,
        conversation_id=payload.conversation_id,
        user_id=actor.id,
        top_k=payload.top_k,
        score_threshold=payload.score_threshold,
        document_id=payload.document_id,
        category_id=payload.category_id,
        brand=payload.brand,
        doc_type=payload.doc_type,
        allow_general_knowledge=payload.allow_general_knowledge,
    )


# --------------------------------------------------------------------------- #
# Admin — static paths before /{conversation_id}.
# --------------------------------------------------------------------------- #
@router.get(
    "/stats",
    response_model=RagStatsRead,
    summary="RAG usage statistics",
)
def rag_stats(
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """Token usage and latency summary across all RAG queries."""
    return RAGEngine(db).stats()


@router.get(
    "/config",
    response_model=RagConfigRead,
    summary="Active RAG configuration",
)
def rag_config(
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """The active provider/model and retrieval settings (no secrets)."""
    settings = get_settings()
    if settings.llm_provider == "claude":
        model, configured = settings.claude_model, bool(settings.claude_api_key)
    elif settings.llm_provider == "openai":
        model, configured = settings.openai_model, bool(settings.openai_api_key)
    else:
        model, configured = "mock-llm", True
    return {
        "llm_provider": settings.llm_provider,
        "llm_model": model,
        "llm_configured": configured,
        "embedding_model": settings.embedding_model,
        "top_k": settings.rag_top_k,
        "score_threshold": settings.rag_score_threshold,
        "max_context_chars": settings.rag_max_context_chars,
        "max_chunks_per_document": settings.rag_max_chunks_per_document,
        "history_messages": settings.rag_history_messages,
        "allow_general_knowledge": settings.rag_allow_general_knowledge,
    }


@router.get(
    "/messages/{message_id}/debug",
    response_model=RagMessageDebugRead,
    summary="Full debug payload for a message",
)
def message_debug(
    message_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(get_current_active_user)],
):
    """Admin prompt debugger: retrieved chunks, final prompt, sources, usage."""
    return RAGEngine(db).get_message(message_id)


# --------------------------------------------------------------------------- #
# Conversations
# --------------------------------------------------------------------------- #
@router.get(
    "/conversations",
    response_model=PaginatedResponse[ConversationRead],
    summary="List conversations",
)
def list_conversations(
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(get_current_active_user)],
    pagination: Annotated[PaginationDep, Depends(pagination_dep)],
) -> dict:
    """List RAG conversations, most recently active first."""
    items, total = RAGEngine(db).list_conversations(
        page=pagination.page, page_size=pagination.page_size
    )
    pages = (total + pagination.page_size - 1) // pagination.page_size if total else 0
    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "pages": pages,
    }


@router.post(
    "/conversations",
    response_model=ConversationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a conversation",
)
def create_conversation(
    payload: ConversationCreate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(get_current_active_user)],
):
    """Create an empty conversation (a conversation is also created implicitly
    by ``POST /rag/query`` when no ``conversation_id`` is given)."""
    from app.models.rag_conversation import RagConversation

    conversation = RagConversation(
        title=payload.title or "New conversation", user_id=actor.id
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationRead,
    summary="Get a conversation",
)
def get_conversation(
    conversation_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(get_current_active_user)],
):
    """Return one conversation by ID."""
    return RAGEngine(db).get_conversation(conversation_id)


@router.delete(
    "/conversations/{conversation_id}",
    response_model=MessageResponse,
    summary="Delete a conversation",
)
def delete_conversation(
    conversation_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """Delete a conversation and all of its messages."""
    RAGEngine(db).delete_conversation(conversation_id)
    return {"message": "Conversation deleted"}


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[RagMessageRead],
    summary="List a conversation's messages",
)
def list_messages(
    conversation_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User, Depends(get_current_active_user)],
):
    """Return the conversation's messages, oldest first."""
    return RAGEngine(db).list_messages(conversation_id)
