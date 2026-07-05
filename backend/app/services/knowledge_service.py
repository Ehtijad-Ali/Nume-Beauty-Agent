"""Knowledge document + category services (Phase 2.1 ingestion)."""

from __future__ import annotations

import hashlib
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models.category import Category
from app.models.document_chunk import DocumentChunk
from app.models.document_version import DocumentVersion
from app.models.knowledge_document import KnowledgeDocument
from app.repositories.category_repo import CategoryRepository
from app.repositories.knowledge_repo import (
    DocumentChunkRepository,
    DocumentVersionRepository,
    KnowledgeDocumentRepository,
)
from app.schemas.knowledge import (
    CategoryCreate,
    CategoryUpdate,
    KnowledgeDocumentCreate,
    KnowledgeDocumentUpdate,
)
from app.services.ingestion import IngestionError, IngestionPipeline
from app.services.ingestion.parsers import UnsupportedTypeError, detect_doc_type


def _compute_checksum(file_bytes: bytes) -> str:
    """Return the SHA-256 checksum of the given bytes."""
    return hashlib.sha256(file_bytes).hexdigest()


def _slugify(name: str) -> str:
    """Turn a category name into a URL-safe slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "category"


# Keyword rules used to auto-categorise documents when no category is given.
_AUTO_CATEGORY_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("brand-guidelines", ("brand", "logo", "voice", "tone", "identity", "guideline", "style guide")),
    ("product-information", ("product", "ingredient", "spec", "catalog", "catalogue", "sku", "faq")),
    ("marketing-material", ("campaign", "marketing", "promo", "advert", "ad copy", "social", "newsletter")),
    ("reports-analytics", ("report", "analytics", "metric", "kpi", "results", "performance", "survey")),
    ("legal-compliance", ("legal", "policy", "terms", "compliance", "gdpr", "privacy", "contract")),
]


class CategoryService:
    """Business logic for knowledge base categories."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CategoryRepository(db)

    def list(self) -> list[dict[str, Any]]:
        """Return all categories with their document counts."""
        counts = self.repo.document_counts()
        result: list[dict[str, Any]] = []
        for category in self.repo.list_all():
            data = {
                "id": category.id,
                "name": category.name,
                "slug": category.slug,
                "description": category.description,
                "color": category.color,
                "document_count": counts.get(category.id, 0),
                "created_at": category.created_at,
                "updated_at": category.updated_at,
            }
            result.append(data)
        return result

    def get(self, category_id: uuid.UUID) -> Category:
        category = self.repo.get(category_id)
        if not category:
            raise NotFoundError("Category not found")
        return category

    def create(self, payload: CategoryCreate) -> Category:
        slug = _slugify(payload.name)
        if self.repo.get_by_name(payload.name) or self.repo.get_by_slug(slug):
            raise ConflictError(f"Category '{payload.name}' already exists")
        category = self.repo.create(
            {
                "name": payload.name.strip(),
                "slug": slug,
                "description": payload.description,
                "color": payload.color,
            }
        )
        self.db.commit()
        return category

    def update(self, category_id: uuid.UUID, payload: CategoryUpdate) -> Category:
        category = self.get(category_id)
        data = payload.model_dump(exclude_unset=True)
        if "name" in data and data["name"]:
            existing = self.repo.get_by_name(data["name"])
            if existing and existing.id != category.id:
                raise ConflictError(f"Category '{data['name']}' already exists")
            data["slug"] = _slugify(data["name"])
        updated = self.repo.update(category, data)
        self.db.commit()
        return updated

    def delete(self, category_id: uuid.UUID) -> None:
        """Delete a category. Documents keep existing (category set to NULL)."""
        category = self.get(category_id)
        self.repo.delete(category)
        self.db.commit()

    def get_or_create_by_slug(self, slug: str, name: str) -> Category:
        category = self.repo.get_by_slug(slug)
        if category:
            return category
        category = self.repo.create({"name": name, "slug": slug})
        return category

    def suggest_for(self, filename: str, title: str, text_sample: str = "") -> Category | None:
        """Keyword-based auto-categorisation (no AI)."""
        haystack = f"{filename} {title} {text_sample[:2000]}".lower()
        for slug, keywords in _AUTO_CATEGORY_RULES:
            if any(keyword in haystack for keyword in keywords):
                name = slug.replace("-", " ").title()
                return self.get_or_create_by_slug(slug, name)
        return self.repo.get_by_slug("other")


class KnowledgeDocumentService:
    """Business logic for knowledge documents and the ingestion pipeline."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = KnowledgeDocumentRepository(db)
        self.chunk_repo = DocumentChunkRepository(db)
        self.version_repo = DocumentVersionRepository(db)
        self.categories = CategoryService(db)
        self.settings = get_settings()
        self.pipeline = IngestionPipeline()

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #
    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        status: str | None = None,
        doc_type: str | None = None,
        category_id: uuid.UUID | None = None,
        brand: str | None = None,
    ) -> tuple[list[KnowledgeDocument], int]:
        """List documents with filters."""
        filters: dict[str, Any] = {}
        if status:
            filters["status"] = status
        if doc_type:
            filters["doc_type"] = doc_type
        if category_id:
            filters["category_id"] = category_id
        if brand:
            filters["brand"] = brand
        return self.repo.list(
            offset=(page - 1) * page_size,
            limit=page_size,
            filters=filters,
            search=search,
        )

    def get(self, doc_id: uuid.UUID) -> KnowledgeDocument:
        """Return a document by ID or raise."""
        doc = self.repo.get(doc_id)
        if not doc:
            raise NotFoundError("Knowledge document not found")
        return doc

    def list_chunks(
        self, doc_id: uuid.UUID, *, page: int = 1, page_size: int = 50
    ) -> tuple[list[DocumentChunk], int]:
        """Return the chunks of a document (paginated)."""
        self.get(doc_id)  # 404 if missing
        return self.chunk_repo.list_for_document(
            doc_id, offset=(page - 1) * page_size, limit=page_size
        )

    def list_versions(self, doc_id: uuid.UUID) -> list[DocumentVersion]:
        """Return the version history of a document (newest first)."""
        self.get(doc_id)  # 404 if missing
        return self.version_repo.list_for_document(doc_id)

    # ------------------------------------------------------------------ #
    # Ingestion
    # ------------------------------------------------------------------ #
    def upload_document(
        self,
        *,
        filename: str,
        content: bytes,
        mime_type: str,
        title: str | None = None,
        category_id: uuid.UUID | None = None,
        brand: str | None = None,
        tags: str | None = None,
        actor_id: uuid.UUID | None = None,
    ) -> KnowledgeDocument:
        """Store an uploaded file, create the document + v1, and ingest it."""
        self._validate_size(content)
        try:
            doc_type = detect_doc_type(filename, mime_type)
        except UnsupportedTypeError as exc:
            raise BadRequestError(str(exc)) from exc

        rel_path = self._store_file(filename, content)
        checksum = _compute_checksum(content)

        category = self.categories.get(category_id) if category_id else None
        if category is None:
            category = self.categories.suggest_for(filename, title or filename)

        doc = self.repo.create(
            {
                "title": (title or Path(filename).stem or filename).strip()[:500],
                "doc_type": doc_type,
                "file_path": rel_path,
                "file_size": len(content),
                "checksum": checksum,
                "status": "processing",
                "tags": tags,
                "brand": brand,
                "version": 1,
                "original_filename": filename[:500],
                "mime_type": mime_type[:255],
                "category_id": category.id if category else None,
                "uploaded_by_id": actor_id,
            }
        )
        self.version_repo.create(
            {
                "document_id": doc.id,
                "version": 1,
                "file_path": rel_path,
                "file_size": len(content),
                "checksum": checksum,
                "original_filename": filename[:500],
                "mime_type": mime_type[:255],
                "change_note": "Initial upload",
                "uploaded_by_id": actor_id,
            }
        )

        self._ingest(doc, content)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def replace_document(
        self,
        doc_id: uuid.UUID,
        *,
        filename: str,
        content: bytes,
        mime_type: str,
        change_note: str | None = None,
        actor_id: uuid.UUID | None = None,
    ) -> KnowledgeDocument:
        """Replace a document's file: bump version, keep history, re-ingest."""
        doc = self.get(doc_id)
        self._validate_size(content)
        try:
            doc_type = detect_doc_type(filename, mime_type)
        except UnsupportedTypeError as exc:
            raise BadRequestError(str(exc)) from exc

        rel_path = self._store_file(filename, content)
        checksum = _compute_checksum(content)
        new_version = (doc.version or 1) + 1

        self.version_repo.create(
            {
                "document_id": doc.id,
                "version": new_version,
                "file_path": rel_path,
                "file_size": len(content),
                "checksum": checksum,
                "original_filename": filename[:500],
                "mime_type": mime_type[:255],
                "change_note": change_note or "File replaced",
                "uploaded_by_id": actor_id,
            }
        )
        self.repo.update(
            doc,
            {
                "doc_type": doc_type,
                "file_path": rel_path,
                "file_size": len(content),
                "checksum": checksum,
                "version": new_version,
                "original_filename": filename[:500],
                "mime_type": mime_type[:255],
                "status": "processing",
            },
        )

        self._ingest(doc, content)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def reindex_document(self, doc_id: uuid.UUID) -> KnowledgeDocument:
        """Re-run the ingestion pipeline on the current stored file."""
        doc = self.get(doc_id)
        if not doc.file_path:
            raise BadRequestError("Document has no stored file to re-index")
        abs_path = self.settings.upload_dir / doc.file_path
        if not abs_path.exists():
            raise BadRequestError("Stored file is missing from disk")
        content = abs_path.read_bytes()
        self._ingest(doc, content)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def _ingest(self, doc: KnowledgeDocument, content: bytes) -> None:
        """Run parse → clean → chunk and persist the outcome on ``doc``."""
        self.chunk_repo.delete_for_document(doc.id)
        try:
            result = self.pipeline.run(
                content,
                doc.original_filename or doc.title,
                doc.mime_type,
                doc_type=doc.doc_type,
            )
        except IngestionError as exc:
            self.repo.update(
                doc,
                {
                    "status": "failed",
                    "error_message": str(exc),
                    "chunk_count": 0,
                    "embedding_status": "none",
                    "vector_count": 0,
                },
            )
            self._purge_vectors(doc.id)
            return

        for chunk in result.chunks:
            self.chunk_repo.create(
                {
                    "document_id": doc.id,
                    "chunk_index": chunk.index,
                    "content": chunk.content,
                    "char_count": len(chunk.content),
                    "word_count": len(chunk.content.split()),
                    "chunk_metadata": chunk.metadata,
                }
            )
        self.repo.update(
            doc,
            {
                "status": "ready",
                "error_message": None,
                "excerpt": result.excerpt,
                "page_count": result.page_count,
                "word_count": result.word_count,
                "char_count": result.char_count,
                "chunk_count": len(result.chunks),
                "doc_metadata": result.metadata or None,
                "last_indexed_at": datetime.now(timezone.utc),
                # The embedding job (scheduled by the endpoint) takes it from here
                "embedding_status": "pending",
            },
        )

    # ------------------------------------------------------------------ #
    # CRUD (record-level, kept from Phase 1)
    # ------------------------------------------------------------------ #
    def create(
        self,
        payload: KnowledgeDocumentCreate,
        *,
        actor_id: uuid.UUID | None = None,
    ) -> KnowledgeDocument:
        """Create a knowledge document record (no file content)."""
        data = payload.model_dump()
        if actor_id:
            data["uploaded_by_id"] = actor_id
        doc = self.repo.create(data)
        self.db.commit()
        return doc

    def update(self, doc_id: uuid.UUID, payload: KnowledgeDocumentUpdate) -> KnowledgeDocument:
        """Update a knowledge document's metadata."""
        doc = self.get(doc_id)
        data = payload.model_dump(exclude_unset=True)
        if data.get("category_id"):
            self.categories.get(data["category_id"])  # 404 if bad
        updated = self.repo.update(doc, data)
        self.db.commit()
        return updated

    def delete(self, doc_id: uuid.UUID) -> None:
        """Delete a document, its chunks/versions, and all stored files."""
        doc = self.get(doc_id)
        paths = {v.file_path for v in self.version_repo.list_for_document(doc_id) if v.file_path}
        if doc.file_path:
            paths.add(doc.file_path)
        self.repo.delete(doc)  # chunks + versions cascade
        self.db.commit()
        self._purge_vectors(doc_id)
        # Best-effort file removal after the DB delete succeeds
        for rel_path in paths:
            try:
                abs_path = self.settings.upload_dir / rel_path
                if abs_path.exists():
                    abs_path.unlink()
            except OSError:
                pass

    def get_file_path(self, doc_id: uuid.UUID) -> Path:
        """Return the absolute path of the document's current file."""
        doc = self.get(doc_id)
        if not doc.file_path:
            raise BadRequestError("Document has no stored file")
        abs_path = self.settings.upload_dir / doc.file_path
        if not abs_path.exists():
            raise NotFoundError("Stored file is missing from disk")
        return abs_path

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _purge_vectors(self, doc_id: uuid.UUID) -> None:
        """Best-effort removal of a document's vectors from Qdrant."""
        from app.services.embedding_service import EmbeddingService

        EmbeddingService(self.db).delete_document_vectors(doc_id)

    def _validate_size(self, content: bytes) -> None:
        if not content:
            raise BadRequestError("File is empty")
        if len(content) > self.settings.max_upload_size_bytes:
            raise BadRequestError(
                f"File exceeds maximum size of {self.settings.max_upload_size_mb} MB"
            )

    def _store_file(self, filename: str, content: bytes) -> str:
        """Persist bytes under uploads/knowledge/<year>/<month>/ and return the relative path."""
        now = datetime.now(timezone.utc)
        rel_dir = Path("knowledge") / str(now.year) / now.strftime("%m")
        abs_dir = self.settings.upload_dir / rel_dir
        abs_dir.mkdir(parents=True, exist_ok=True)

        safe_name = f"{uuid.uuid4().hex}_{Path(filename).name}"
        (abs_dir / safe_name).write_bytes(content)
        return str(rel_dir / safe_name)
