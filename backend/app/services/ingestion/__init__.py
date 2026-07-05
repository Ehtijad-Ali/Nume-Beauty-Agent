"""
Document ingestion pipeline — Phase 2.1.

Parses uploaded files (PDF, DOCX, TXT, CSV, images via pluggable OCR),
cleans and normalises the extracted text, extracts metadata, and splits the
result into chunks ready for indexing in a later phase.

No embeddings, vector stores, or AI providers are involved here.
"""

from app.services.ingestion.pipeline import IngestionError, IngestionPipeline, IngestionResult
from app.services.ingestion.parsers import ParsedDocument, get_parser, detect_doc_type, SUPPORTED_DOC_TYPES

__all__ = [
    "IngestionError",
    "IngestionPipeline",
    "IngestionResult",
    "ParsedDocument",
    "get_parser",
    "detect_doc_type",
    "SUPPORTED_DOC_TYPES",
]
