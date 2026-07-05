"""RAG engine — Phase 2.3.

Orchestrates the full retrieval-augmented generation flow:

    user prompt → semantic search → retrieve chunks → build context
    → inject brand context → build prompt (+ conversation memory)
    → send to the LLM → persist + return the answer with citations.

Every exchange is persisted with its complete debug payload (retrieved
chunks, final prompt, sources, similarity scores, token usage, timings) so
the admin panel can inspect exactly what the model saw.
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.ai.providers import get_llm_provider
from app.config.settings import get_settings
from app.core.exceptions import NotFoundError
from app.models.rag_conversation import RagConversation, RagMessage
from app.rag.context_builder import build_context
from app.rag.prompt_builder import (
    build_brand_context,
    build_messages,
    build_system_prompt,
    prompt_debug_payload,
)
from app.rag.retriever import Retriever

logger = logging.getLogger(__name__)

NO_CONTEXT_ANSWER = (
    "I couldn't find anything in the knowledge base relevant to that question. "
    "Try rephrasing it, or upload the document that covers this topic."
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RAGEngine:
    """End-to-end retrieval-augmented generation."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.retriever = Retriever(db)

    # ------------------------------------------------------------------ #
    # Query
    # ------------------------------------------------------------------ #
    def query(
        self,
        question: str,
        *,
        conversation_id: uuid.UUID | None = None,
        user_id: uuid.UUID | None = None,
        top_k: int | None = None,
        score_threshold: float | None = None,
        document_id: uuid.UUID | None = None,
        category_id: uuid.UUID | None = None,
        brand: str | None = None,
        doc_type: str | None = None,
        allow_general_knowledge: bool | None = None,
    ) -> dict[str, Any]:
        """Run one RAG turn and return the full response envelope."""
        started = time.perf_counter()
        allow_general = (
            self.settings.rag_allow_general_knowledge
            if allow_general_knowledge is None
            else allow_general_knowledge
        )

        conversation = self._get_or_create_conversation(
            conversation_id, user_id=user_id, first_question=question
        )
        history = self._load_history(conversation)

        # 1. Semantic search + ranking
        retrieval_started = time.perf_counter()
        chunks = self.retriever.retrieve(
            question,
            top_k=top_k,
            score_threshold=score_threshold,
            document_id=document_id,
            category_id=category_id,
            brand=brand,
            doc_type=doc_type,
        )
        retrieval_ms = round((time.perf_counter() - retrieval_started) * 1000, 1)

        # 2. Context + brand context + prompt
        context, sources = build_context(chunks)
        brand_context = build_brand_context(self.db)
        system = build_system_prompt(
            context=context,
            brand_context=brand_context,
            allow_general_knowledge=allow_general,
        )
        messages = build_messages(history, question)
        final_prompt = prompt_debug_payload(system, messages)

        # 3. LLM call — skipped when grounding is strict and nothing was found
        llm_ms = 0.0
        if not chunks and not allow_general:
            answer_text = NO_CONTEXT_ANSWER
            provider_name, model_name = "none", None
            input_tokens = output_tokens = 0
        else:
            provider = get_llm_provider()
            llm_started = time.perf_counter()
            result = provider.complete(system=system, messages=messages)
            llm_ms = round((time.perf_counter() - llm_started) * 1000, 1)
            answer_text = result.text
            provider_name, model_name = result.provider, result.model
            input_tokens, output_tokens = result.input_tokens, result.output_tokens

        total_ms = round((time.perf_counter() - started) * 1000, 1)

        # 4. Persist the exchange (user turn + assistant turn with debug data)
        user_message = RagMessage(
            conversation_id=conversation.id,
            role="user",
            content=question,
            sequence=conversation.message_count + 1,
        )
        assistant_message = RagMessage(
            conversation_id=conversation.id,
            role="assistant",
            sequence=conversation.message_count + 2,
            content=answer_text,
            provider=provider_name,
            model=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            retrieval_ms=retrieval_ms,
            llm_ms=llm_ms,
            total_ms=total_ms,
            retrieved_chunks=chunks,
            sources=sources,
            final_prompt=final_prompt,
            rag_metadata={
                "allow_general_knowledge": allow_general,
                "top_k": top_k or self.settings.rag_top_k,
                "score_threshold": (
                    self.settings.rag_score_threshold
                    if score_threshold is None
                    else score_threshold
                ),
                "filters": {
                    "document_id": str(document_id) if document_id else None,
                    "category_id": str(category_id) if category_id else None,
                    "brand": brand,
                    "doc_type": doc_type,
                },
                "history_messages": len(history),
            },
        )
        conversation.message_count += 2
        conversation.total_input_tokens += input_tokens
        conversation.total_output_tokens += output_tokens
        conversation.last_message_at = _utcnow()
        self.db.add_all([user_message, assistant_message])
        self.db.commit()
        self.db.refresh(assistant_message)

        return {
            "conversation_id": conversation.id,
            "message_id": assistant_message.id,
            "answer": answer_text,
            "sources": sources,
            "retrieved_chunks": chunks,
            "final_prompt": final_prompt,
            "provider": provider_name,
            "model": model_name,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
            },
            "timings": {
                "retrieval_ms": retrieval_ms,
                "llm_ms": llm_ms,
                "total_ms": total_ms,
            },
        }

    # ------------------------------------------------------------------ #
    # Conversation memory
    # ------------------------------------------------------------------ #
    def _get_or_create_conversation(
        self,
        conversation_id: uuid.UUID | None,
        *,
        user_id: uuid.UUID | None,
        first_question: str,
    ) -> RagConversation:
        if conversation_id is not None:
            conversation = self.db.get(RagConversation, conversation_id)
            if conversation is None:
                raise NotFoundError("Conversation not found")
            return conversation
        conversation = RagConversation(
            title=first_question.strip()[:120] or "New conversation",
            user_id=user_id,
        )
        self.db.add(conversation)
        self.db.flush()
        return conversation

    def _load_history(self, conversation: RagConversation) -> list[dict[str, str]]:
        """Last N turns of the conversation, oldest first."""
        limit = self.settings.rag_history_messages
        if limit <= 0:
            return []
        rows = (
            self.db.query(RagMessage)
            .filter(RagMessage.conversation_id == conversation.id)
            .order_by(RagMessage.sequence.desc())
            .limit(limit)
            .all()
        )
        return [{"role": r.role, "content": r.content} for r in reversed(rows)]

    # ------------------------------------------------------------------ #
    # Conversations API
    # ------------------------------------------------------------------ #
    def list_conversations(self, *, page: int, page_size: int) -> tuple[list[RagConversation], int]:
        query = self.db.query(RagConversation).order_by(
            RagConversation.last_message_at.desc().nullslast(),
            RagConversation.created_at.desc(),
        )
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def get_conversation(self, conversation_id: uuid.UUID) -> RagConversation:
        conversation = self.db.get(RagConversation, conversation_id)
        if conversation is None:
            raise NotFoundError("Conversation not found")
        return conversation

    def delete_conversation(self, conversation_id: uuid.UUID) -> None:
        self.db.delete(self.get_conversation(conversation_id))
        self.db.commit()

    def list_messages(self, conversation_id: uuid.UUID) -> list[RagMessage]:
        self.get_conversation(conversation_id)
        return (
            self.db.query(RagMessage)
            .filter(RagMessage.conversation_id == conversation_id)
            .order_by(RagMessage.sequence)
            .all()
        )

    def get_message(self, message_id: uuid.UUID) -> RagMessage:
        message = self.db.get(RagMessage, message_id)
        if message is None:
            raise NotFoundError("Message not found")
        return message

    # ------------------------------------------------------------------ #
    # Admin stats
    # ------------------------------------------------------------------ #
    def stats(self) -> dict[str, Any]:
        """Token usage and latency summary for the admin panel."""
        totals = (
            self.db.query(
                func.count(RagMessage.id),
                func.coalesce(func.sum(RagMessage.input_tokens), 0),
                func.coalesce(func.sum(RagMessage.output_tokens), 0),
                func.avg(RagMessage.total_ms),
                func.avg(RagMessage.retrieval_ms),
                func.avg(RagMessage.llm_ms),
            )
            .filter(RagMessage.role == "assistant")
            .one()
        )
        by_model = (
            self.db.query(
                RagMessage.provider,
                RagMessage.model,
                func.count(RagMessage.id),
                func.coalesce(func.sum(RagMessage.input_tokens), 0),
                func.coalesce(func.sum(RagMessage.output_tokens), 0),
            )
            .filter(RagMessage.role == "assistant", RagMessage.provider.isnot(None))
            .group_by(RagMessage.provider, RagMessage.model)
            .all()
        )
        count, in_tokens, out_tokens, avg_total, avg_retrieval, avg_llm = totals
        return {
            "conversation_count": self.db.query(func.count(RagConversation.id)).scalar() or 0,
            "query_count": count,
            "total_input_tokens": int(in_tokens),
            "total_output_tokens": int(out_tokens),
            "total_tokens": int(in_tokens) + int(out_tokens),
            "avg_total_ms": round(float(avg_total), 1) if avg_total is not None else None,
            "avg_retrieval_ms": round(float(avg_retrieval), 1) if avg_retrieval is not None else None,
            "avg_llm_ms": round(float(avg_llm), 1) if avg_llm is not None else None,
            "by_model": [
                {
                    "provider": provider,
                    "model": model,
                    "queries": queries,
                    "input_tokens": int(itok),
                    "output_tokens": int(otok),
                }
                for provider, model, queries, itok, otok in by_model
            ],
        }
