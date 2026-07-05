"""Vector index state — Phase 2.2.

Adds embedding/index tracking columns to knowledge_documents. Vectors
themselves live in Qdrant; PostgreSQL only tracks per-document status.

Revision ID: 0003_vector_index
Revises: 0002_knowledge_base
Create Date: 2026-07-04 00:00:00

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_vector_index"
down_revision: Union[str, None] = "0002_knowledge_base"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "knowledge_documents",
        sa.Column("embedding_status", sa.String(20), nullable=False, server_default="none"),
    )
    op.add_column("knowledge_documents", sa.Column("embedding_error", sa.Text(), nullable=True))
    op.add_column("knowledge_documents", sa.Column("embedding_model", sa.String(200), nullable=True))
    op.add_column(
        "knowledge_documents",
        sa.Column("embedded_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "knowledge_documents",
        sa.Column("vector_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index(
        "ix_knowledge_documents_embedding_status", "knowledge_documents", ["embedding_status"]
    )


def downgrade() -> None:
    op.drop_index("ix_knowledge_documents_embedding_status", table_name="knowledge_documents")
    for column in ("vector_count", "embedded_at", "embedding_model", "embedding_error", "embedding_status"):
        op.drop_column("knowledge_documents", column)
