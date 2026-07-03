"""Initial schema — Phase 1.1.

Creates all 13 tables: roles, users, sessions, products, knowledge_documents,
campaigns, generated_contents, brand_guidelines, competitors, customer_reviews,
uploads, settings, audit_logs.

Uses dialect-agnostic types so the migration works on both PostgreSQL (prod)
and SQLite (tests). On PostgreSQL, Uuid renders as native UUID and the JSON
variant is JSONB.

Revision ID: 0001_initial
Revises:
Create Date: 2025-01-01 00:00:00

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Uuid
from sqlalchemy.types import JSON
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# JSON type that uses JSONB on PostgreSQL and plain JSON elsewhere (tests).
_JSON_TYPE = JSONB().with_variant(JSON(), "sqlite")


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # roles
    # ------------------------------------------------------------------ #
    op.create_table(
        "roles",
        sa.Column("id", Uuid, primary_key=True, nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("name", name="uq_roles_name"),
    )
    op.create_index("ix_roles_name", "roles", ["name"])

    # ------------------------------------------------------------------ #
    # users
    # ------------------------------------------------------------------ #
    op.create_table(
        "users",
        sa.Column("id", Uuid, primary_key=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("avatar_url", sa.String(512), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("role_id", Uuid, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role_id", "users", ["role_id"])

    # ------------------------------------------------------------------ #
    # sessions
    # ------------------------------------------------------------------ #
    op.create_table(
        "sessions",
        sa.Column("id", Uuid, primary_key=True, nullable=False),
        sa.Column("user_id", Uuid, nullable=False),
        sa.Column("refresh_token_jti", sa.String(64), nullable=False),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("refresh_token_jti", name="uq_sessions_jti"),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
    op.create_index("ix_sessions_refresh_token_jti", "sessions", ["refresh_token_jti"])

    # ------------------------------------------------------------------ #
    # products
    # ------------------------------------------------------------------ #
    op.create_table(
        "products",
        sa.Column("id", Uuid, primary_key=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("sku", sa.String(100), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("stock", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("image_url", sa.String(512), nullable=True),
        sa.Column("metadata_json", _JSON_TYPE, nullable=True),
        sa.Column("owner_id", Uuid, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("sku", name="uq_products_sku"),
    )
    op.create_index("ix_products_name", "products", ["name"])
    op.create_index("ix_products_sku", "products", ["sku"])
    op.create_index("ix_products_category", "products", ["category"])
    op.create_index("ix_products_status", "products", ["status"])
    op.create_index("ix_products_owner_id", "products", ["owner_id"])

    # ------------------------------------------------------------------ #
    # knowledge_documents
    # ------------------------------------------------------------------ #
    op.create_table(
        "knowledge_documents",
        sa.Column("id", Uuid, primary_key=True, nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("doc_type", sa.String(20), nullable=False),
        sa.Column("source_url", sa.String(1024), nullable=True),
        sa.Column("file_path", sa.String(1024), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("checksum", sa.String(128), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("tags", sa.Text(), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column("uploaded_by_id", Uuid, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["uploaded_by_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_knowledge_documents_title", "knowledge_documents", ["title"])
    op.create_index("ix_knowledge_documents_doc_type", "knowledge_documents", ["doc_type"])
    op.create_index("ix_knowledge_documents_status", "knowledge_documents", ["status"])
    op.create_index("ix_knowledge_documents_uploaded_by_id", "knowledge_documents", ["uploaded_by_id"])

    # ------------------------------------------------------------------ #
    # campaigns
    # ------------------------------------------------------------------ #
    op.create_table(
        "campaigns",
        sa.Column("id", Uuid, primary_key=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("channel", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("budget", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("spent", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("impressions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("clicks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("conversions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("owner_id", Uuid, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_campaigns_name", "campaigns", ["name"])
    op.create_index("ix_campaigns_channel", "campaigns", ["channel"])
    op.create_index("ix_campaigns_status", "campaigns", ["status"])
    op.create_index("ix_campaigns_owner_id", "campaigns", ["owner_id"])

    # ------------------------------------------------------------------ #
    # generated_contents
    # ------------------------------------------------------------------ #
    op.create_table(
        "generated_contents",
        sa.Column("id", Uuid, primary_key=True, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(50), nullable=False),
        sa.Column("channel", sa.String(50), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("prompt", sa.Text(), nullable=True),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column("campaign_id", Uuid, nullable=True),
        sa.Column("product_id", Uuid, nullable=True),
        sa.Column("created_by_id", Uuid, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_generated_contents_title", "generated_contents", ["title"])
    op.create_index("ix_generated_contents_campaign_id", "generated_contents", ["campaign_id"])
    op.create_index("ix_generated_contents_product_id", "generated_contents", ["product_id"])
    op.create_index("ix_generated_contents_created_by_id", "generated_contents", ["created_by_id"])

    # ------------------------------------------------------------------ #
    # brand_guidelines
    # ------------------------------------------------------------------ #
    op.create_table(
        "brand_guidelines",
        sa.Column("id", Uuid, primary_key=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("guideline_type", sa.String(50), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by_id", Uuid, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_brand_guidelines_name", "brand_guidelines", ["name"])

    # ------------------------------------------------------------------ #
    # competitors
    # ------------------------------------------------------------------ #
    op.create_table(
        "competitors",
        sa.Column("id", Uuid, primary_key=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("logo_url", sa.String(512), nullable=True),
        sa.Column("share_of_voice", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("traffic", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("keywords_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ads_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_competitors_name", "competitors", ["name"])
    op.create_index("ix_competitors_domain", "competitors", ["domain"])

    # ------------------------------------------------------------------ #
    # customer_reviews
    # ------------------------------------------------------------------ #
    op.create_table(
        "customer_reviews",
        sa.Column("id", Uuid, primary_key=True, nullable=False),
        sa.Column("author", sa.String(255), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("product_name", sa.String(255), nullable=True),
        sa.Column("sentiment", sa.String(20), nullable=False, server_default="neutral"),
        sa.Column("status", sa.String(20), nullable=False, server_default="new"),
        sa.Column("review_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("response", sa.Text(), nullable=True),
        sa.Column("product_id", Uuid, nullable=True),
        sa.Column("responded_by_id", Uuid, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["responded_by_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_customer_reviews_source", "customer_reviews", ["source"])
    op.create_index("ix_customer_reviews_product_name", "customer_reviews", ["product_name"])
    op.create_index("ix_customer_reviews_sentiment", "customer_reviews", ["sentiment"])
    op.create_index("ix_customer_reviews_status", "customer_reviews", ["status"])
    op.create_index("ix_customer_reviews_product_id", "customer_reviews", ["product_id"])
    op.create_index("ix_customer_reviews_responded_by_id", "customer_reviews", ["responded_by_id"])

    # ------------------------------------------------------------------ #
    # uploads
    # ------------------------------------------------------------------ #
    op.create_table(
        "uploads",
        sa.Column("id", Uuid, primary_key=True, nullable=False),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("original_filename", sa.String(512), nullable=False),
        sa.Column("mime_type", sa.String(255), nullable=False),
        sa.Column("size", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("storage_path", sa.String(1024), nullable=False),
        sa.Column("storage_type", sa.String(20), nullable=False, server_default="local"),
        sa.Column("category", sa.String(50), nullable=False, server_default="other"),
        sa.Column("status", sa.String(20), nullable=False, server_default="completed"),
        sa.Column("checksum", sa.String(128), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("uploaded_by_id", Uuid, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["uploaded_by_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_uploads_filename", "uploads", ["filename"])
    op.create_index("ix_uploads_category", "uploads", ["category"])
    op.create_index("ix_uploads_status", "uploads", ["status"])
    op.create_index("ix_uploads_uploaded_by_id", "uploads", ["uploaded_by_id"])

    # ------------------------------------------------------------------ #
    # settings
    # ------------------------------------------------------------------ #
    op.create_table(
        "settings",
        sa.Column("id", Uuid, primary_key=True, nullable=False),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("category", sa.String(50), nullable=False, server_default="general"),
        sa.Column("is_sensitive", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("updated_by_id", Uuid, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("key", name="uq_settings_key"),
    )
    op.create_index("ix_settings_key", "settings", ["key"])
    op.create_index("ix_settings_category", "settings", ["category"])
    op.create_index("ix_settings_updated_by_id", "settings", ["updated_by_id"])

    # ------------------------------------------------------------------ #
    # audit_logs
    # ------------------------------------------------------------------ #
    op.create_table(
        "audit_logs",
        sa.Column("id", Uuid, primary_key=True, nullable=False),
        sa.Column("user_id", Uuid, nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=True),
        sa.Column("resource_id", sa.String(100), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("details", _JSON_TYPE, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_resource_type", "audit_logs", ["resource_type"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("settings")
    op.drop_table("uploads")
    op.drop_table("customer_reviews")
    op.drop_table("competitors")
    op.drop_table("brand_guidelines")
    op.drop_table("generated_contents")
    op.drop_table("campaigns")
    op.drop_table("knowledge_documents")
    op.drop_table("products")
    op.drop_table("sessions")
    op.drop_table("users")
    op.drop_table("roles")
