"""RAG conversation models — Phase 2.3.

``RagConversation`` groups a chat thread; ``RagMessage`` stores each turn
along with the full debug payload (retrieved chunks, final prompt, sources,
token usage, timings) so the admin panel can replay any exchange.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.user import User

# JSONB on PostgreSQL, plain JSON on SQLite (for tests).
_json_type = JSONB().with_variant(JSON(), "sqlite")


class RagConversation(Base, UUIDPKMixin, TimestampMixin):
    """A chat thread with the RAG assistant."""

    __tablename__ = "rag_conversations"

    title: Mapped[str] = mapped_column(String(500), default="New conversation", nullable=False)
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_input_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_output_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    user: Mapped["User | None"] = relationship(lazy="joined")
    # ORM-level cascade so deletes also work on SQLite tests.
    messages: Mapped[list["RagMessage"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="RagMessage.sequence",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<RagConversation {self.title}>"


class RagMessage(Base, UUIDPKMixin, TimestampMixin):
    """One turn in a RAG conversation (user question or assistant answer)."""

    __tablename__ = "rag_messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("rag_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user | assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Position within the conversation — created_at only has second precision.
    sequence: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # --- assistant-turn metadata (null on user turns) ---
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model: Mapped[str | None] = mapped_column(String(200), nullable=True)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    retrieval_ms: Mapped[float | None] = mapped_column(nullable=True)
    llm_ms: Mapped[float | None] = mapped_column(nullable=True)
    total_ms: Mapped[float | None] = mapped_column(nullable=True)

    # --- admin/debug payloads ---
    retrieved_chunks: Mapped[list[dict[str, Any]] | None] = mapped_column(_json_type, nullable=True)
    sources: Mapped[list[dict[str, Any]] | None] = mapped_column(_json_type, nullable=True)
    final_prompt: Mapped[dict[str, Any] | None] = mapped_column(_json_type, nullable=True)
    rag_metadata: Mapped[dict[str, Any] | None] = mapped_column(_json_type, nullable=True)

    conversation: Mapped[RagConversation] = relationship(back_populates="messages")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<RagMessage {self.role}>"
