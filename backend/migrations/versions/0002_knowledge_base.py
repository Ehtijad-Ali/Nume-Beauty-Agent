"""Knowledge Base document management — Phase 2.1.

Creates the categories, document_versions and document_chunks tables and
extends knowledge_documents with ingestion metadata (brand, version,
category, counts, parsed metadata, error message, last indexed timestamp).

Uses dialect-agnostic types so the migration works on both PostgreSQL (prod)
and SQLite (tests). On PostgreSQL the JSON variant is JSONB.

Revision ID: 0002_knowledge_base
Revises: 0001_initial
Create Date: 2026-07-04 00:00:00

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Uuid
from sqlalchemy.types import JSON
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "0002_knowledge_base"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# JSON type that uses JSONB on PostgreSQL and plain JSON elsewhere (tests).
_JSON_TYPE = JSONB().with_variant(JSON(), "sqlite")


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # categories
    # ------------------------------------------------------------------ #
    op.create_table(
        "categories",
        sa.Column("id", Uuid, primary_key=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("color", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("name", name="uq_categories_name"),
        sa.UniqueConstraint("slug", name="uq_categories_slug"),
    )
    op.create_index("ix_categories_name", "categories", ["name"])
    op.create_index("ix_categories_slug", "categories", ["slug"])

    # ------------------------------------------------------------------ #
    # knowledge_documents — new columns
    # ------------------------------------------------------------------ #
    op.add_column("knowledge_documents", sa.Column("original_filename", sa.String(500), nullable=True))
    op.add_column("knowledge_documents", sa.Column("mime_type", sa.String(255), nullable=True))
    op.add_column("knowledge_documents", sa.Column("brand", sa.String(200), nullable=True))
    op.add_column("knowledge_documents", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("knowledge_documents", sa.Column("language", sa.String(20), nullable=True))
    op.add_column("knowledge_documents", sa.Column("page_count", sa.Integer(), nullable=True))
    op.add_column("knowledge_documents", sa.Column("word_count", sa.Integer(), nullable=True))
    op.add_column("knowledge_documents", sa.Column("char_count", sa.Integer(), nullable=True))
    op.add_column("knowledge_documents", sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("knowledge_documents", sa.Column("doc_metadata", _JSON_TYPE, nullable=True))
    op.add_column("knowledge_documents", sa.Column("error_message", sa.Text(), nullable=True))
    op.add_column("knowledge_documents", sa.Column("last_indexed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("knowledge_documents", sa.Column("category_id", Uuid, nullable=True))
    op.create_index("ix_knowledge_documents_brand", "knowledge_documents", ["brand"])
    op.create_index("ix_knowledge_documents_category_id", "knowledge_documents", ["category_id"])
    op.create_foreign_key(
        "fk_knowledge_documents_category_id",
        "knowledge_documents",
        "categories",
        ["category_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ------------------------------------------------------------------ #
    # document_versions
    # ------------------------------------------------------------------ #
    op.create_table(
        "document_versions",
        sa.Column("id", Uuid, primary_key=True, nullable=False),
        sa.Column("document_id", Uuid, sa.ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("file_path", sa.String(1024), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("checksum", sa.String(128), nullable=True),
        sa.Column("original_filename", sa.String(500), nullable=True),
        sa.Column("mime_type", sa.String(255), nullable=True),
        sa.Column("change_note", sa.Text(), nullable=True),
        sa.Column("uploaded_by_id", Uuid, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("document_id", "version", name="uq_document_versions_doc_ver"),
    )
    op.create_index("ix_document_versions_document_id", "document_versions", ["document_id"])
    op.create_index("ix_document_versions_uploaded_by_id", "document_versions", ["uploaded_by_id"])

    # ------------------------------------------------------------------ #
    # document_chunks
    # ------------------------------------------------------------------ #
    op.create_table(
        "document_chunks",
        sa.Column("id", Uuid, primary_key=True, nullable=False),
        sa.Column("document_id", Uuid, sa.ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("char_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("word_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("chunk_metadata", _JSON_TYPE, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_document_chunks_doc_idx"),
    )
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"])


def downgrade() -> None:
    op.drop_index("ix_document_chunks_document_id", table_name="document_chunks")
    op.drop_table("document_chunks")

    op.drop_index("ix_document_versions_uploaded_by_id", table_name="document_versions")
    op.drop_index("ix_document_versions_document_id", table_name="document_versions")
    op.drop_table("document_versions")

    op.drop_constraint("fk_knowledge_documents_category_id", "knowledge_documents", type_="foreignkey")
    op.drop_index("ix_knowledge_documents_category_id", table_name="knowledge_documents")
    op.drop_index("ix_knowledge_documents_brand", table_name="knowledge_documents")
    for column in (
        "category_id",
        "last_indexed_at",
        "error_message",
        "doc_metadata",
        "chunk_count",
        "char_count",
        "word_count",
        "page_count",
        "language",
        "version",
        "brand",
        "mime_type",
        "original_filename",
    ):
        op.drop_column("knowledge_documents", column)

    op.drop_index("ix_categories_slug", table_name="categories")
    op.drop_index("ix_categories_name", table_name="categories")
    op.drop_table("categories")
