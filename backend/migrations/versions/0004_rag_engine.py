"""RAG engine — Phase 2.3.

Adds conversation memory tables: rag_conversations and rag_messages.
Assistant messages carry the full debug payload (retrieved chunks, final
prompt, sources, token usage, timings) as JSONB.

Revision ID: 0004_rag_engine
Revises: 0003_vector_index
Create Date: 2026-07-04 00:00:00

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "0004_rag_engine"
down_revision: Union[str, None] = "0003_vector_index"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rag_conversations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False, server_default="New conversation"),
        sa.Column("message_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rag_conversations_user_id", "rag_conversations", ["user_id"])

    op.create_table(
        "rag_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("provider", sa.String(50), nullable=True),
        sa.Column("model", sa.String(200), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("retrieval_ms", sa.Float(), nullable=True),
        sa.Column("llm_ms", sa.Float(), nullable=True),
        sa.Column("total_ms", sa.Float(), nullable=True),
        sa.Column("retrieved_chunks", JSONB(), nullable=True),
        sa.Column("sources", JSONB(), nullable=True),
        sa.Column("final_prompt", JSONB(), nullable=True),
        sa.Column("rag_metadata", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["rag_conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rag_messages_conversation_id", "rag_messages", ["conversation_id"])


def downgrade() -> None:
    op.drop_index("ix_rag_messages_conversation_id", table_name="rag_messages")
    op.drop_table("rag_messages")
    op.drop_index("ix_rag_conversations_user_id", table_name="rag_conversations")
    op.drop_table("rag_conversations")
