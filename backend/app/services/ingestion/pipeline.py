"""Ingestion pipeline orchestrator.

Runs the full pure-Python ingestion sequence on a file:

    parse → clean/normalise → extract metadata → chunk

Chunk size/overlap adapt to the document type (see ``CHUNK_PROFILES``), and
page-based formats (PDF) chunk per page so every chunk carries its page
number. The pipeline is stateless and DB-agnostic; persisting the result to
the ``knowledge_documents`` / ``document_chunks`` tables is the job of
:class:`app.services.knowledge_service.KnowledgeDocumentService`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.ingestion.chunking import (
    TextChunk,
    chunk_profile,
    chunk_text,
)
from app.services.ingestion.cleaning import clean_and_normalize, make_excerpt, word_count
from app.services.ingestion.parsers import ParserError, detect_doc_type, get_parser


class IngestionError(Exception):
    """Raised when a document cannot be ingested."""


@dataclass
class IngestionResult:
    """Everything extracted from one document."""

    doc_type: str
    text: str
    excerpt: str
    chunks: list[TextChunk]
    metadata: dict[str, Any] = field(default_factory=dict)
    page_count: int | None = None
    word_count: int = 0
    char_count: int = 0


class IngestionPipeline:
    """Parse, clean, and chunk a document's raw bytes."""

    def __init__(
        self,
        *,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> None:
        # None = pick a smart per-doc-type profile at run time.
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def run(
        self,
        content: bytes,
        filename: str,
        mime_type: str | None = None,
        doc_type: str | None = None,
    ) -> IngestionResult:
        """Ingest one file. Raises :class:`IngestionError` on failure."""
        if not content:
            raise IngestionError("File is empty")

        try:
            resolved_type = doc_type or detect_doc_type(filename, mime_type)
            parser = get_parser(resolved_type)
            parsed = parser.parse(content, filename)
        except ParserError as exc:
            raise IngestionError(str(exc)) from exc

        text = clean_and_normalize(parsed.text)
        if not text:
            raise IngestionError("Document contains no readable text after cleaning")

        profile_size, profile_overlap = chunk_profile(resolved_type)
        size = self.chunk_size or profile_size
        overlap = self.chunk_overlap if self.chunk_overlap is not None else profile_overlap

        if parsed.pages:
            # Chunk page by page so each chunk knows its page number.
            chunks: list[TextChunk] = []
            for page_number, page_text in enumerate(parsed.pages, start=1):
                cleaned_page = clean_and_normalize(page_text)
                if not cleaned_page:
                    continue
                for chunk in chunk_text(cleaned_page, chunk_size=size, overlap=overlap):
                    chunks.append(
                        TextChunk(
                            index=len(chunks),
                            content=chunk.content,
                            metadata={"page": page_number},
                        )
                    )
        else:
            chunks = chunk_text(text, chunk_size=size, overlap=overlap)

        return IngestionResult(
            doc_type=resolved_type,
            text=text,
            excerpt=make_excerpt(text),
            chunks=chunks,
            metadata=parsed.metadata,
            page_count=parsed.page_count,
            word_count=word_count(text),
            char_count=len(text),
        )
