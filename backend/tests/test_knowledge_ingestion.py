"""Tests for the Phase 2.1 ingestion pipeline (parsers, cleaning, chunking)."""

from __future__ import annotations

import io

import pytest

from app.services.ingestion import IngestionError, IngestionPipeline, detect_doc_type
from app.services.ingestion.chunking import chunk_text
from app.services.ingestion.cleaning import clean_and_normalize, clean_text, make_excerpt
from app.services.ingestion.parsers import (
    CsvParser,
    ParserError,
    TxtParser,
    UnsupportedTypeError,
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def make_pdf(text: str) -> bytes:
    """Build a minimal valid single-page PDF containing ``text``."""
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(out.tell())
        out.write(f"{i} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref_pos = out.tell()
    out.write(f"xref\n0 {len(objects) + 1}\n".encode())
    out.write(b"0000000000 65535 f \n")
    for off in offsets:
        out.write(f"{off:010d} 00000 n \n".encode())
    out.write(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_pos}\n%%EOF".encode()
    )
    return out.getvalue()


def make_docx(paragraphs: list[str]) -> bytes:
    """Build a real DOCX in memory via python-docx."""
    import docx

    document = docx.Document()
    for p in paragraphs:
        document.add_paragraph(p)
    buf = io.BytesIO()
    document.save(buf)
    return buf.getvalue()


# --------------------------------------------------------------------------- #
# Cleaning / normalisation
# --------------------------------------------------------------------------- #
def test_clean_text_collapses_whitespace_and_control_chars() -> None:
    dirty = "Hello\x00\x0b  world  \r\nline\ttwo\n\n\n\n\nend  "
    cleaned = clean_text(dirty)
    assert "\x00" not in cleaned
    assert "  " not in cleaned
    assert "\n\n\n" not in cleaned
    assert cleaned.startswith("Hello world")
    assert cleaned.endswith("end")


def test_clean_text_repairs_hyphenated_line_breaks() -> None:
    assert clean_text("market-\ning plan") == "marketing plan"


def test_normalize_smart_punctuation() -> None:
    assert clean_and_normalize("“Hello” — it’s fine…") == '"Hello" - it\'s fine...'


def test_make_excerpt_truncates_on_word_boundary() -> None:
    text = "word " * 300
    excerpt = make_excerpt(text, max_chars=100)
    assert len(excerpt) <= 101  # +1 for the ellipsis
    assert excerpt.endswith("…")


# --------------------------------------------------------------------------- #
# Chunking
# --------------------------------------------------------------------------- #
def test_chunk_text_empty_returns_no_chunks() -> None:
    assert chunk_text("") == []
    assert chunk_text("   \n\n  ") == []


def test_chunk_text_small_doc_single_chunk() -> None:
    chunks = chunk_text("A short paragraph.", chunk_size=1000)
    assert len(chunks) == 1
    assert chunks[0].index == 0
    assert chunks[0].content == "A short paragraph."


def test_chunk_text_respects_size_limit_and_orders_indexes() -> None:
    text = "\n\n".join(f"Paragraph {i}. " + ("content " * 40) for i in range(20))
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    assert len(chunks) > 1
    assert all(len(c.content) <= 500 for c in chunks)
    assert [c.index for c in chunks] == list(range(len(chunks)))


def test_chunk_text_splits_oversized_paragraph() -> None:
    text = "This is a sentence. " * 200  # one giant paragraph
    chunks = chunk_text(text, chunk_size=300, overlap=30)
    assert len(chunks) > 1
    assert all(len(c.content) <= 300 for c in chunks)


# --------------------------------------------------------------------------- #
# Parsers
# --------------------------------------------------------------------------- #
def test_detect_doc_type_by_extension_and_mime() -> None:
    assert detect_doc_type("guide.PDF") == "pdf"
    assert detect_doc_type("notes.docx") == "docx"
    assert detect_doc_type("data.csv") == "csv"
    assert detect_doc_type("readme.md") == "md"
    assert detect_doc_type("photo.jpeg") == "image"
    assert detect_doc_type("noext", "text/plain") == "txt"
    assert detect_doc_type("noext", "image/png") == "image"
    with pytest.raises(UnsupportedTypeError):
        detect_doc_type("archive.zip")


def test_txt_parser_decodes_utf8_and_fallback() -> None:
    parser = TxtParser()
    assert parser.parse("héllo".encode("utf-8"), "a.txt").text == "héllo"
    assert "caf" in parser.parse("café".encode("latin-1"), "a.txt").text


def test_csv_parser_preserves_column_context() -> None:
    content = b"name,price,stock\nAurora Serum,78,100\nVelvet Tint,29,50\n"
    parsed = CsvParser().parse(content, "products.csv")
    assert parsed.metadata["columns"] == ["name", "price", "stock"]
    assert parsed.metadata["row_count"] == 2
    assert "name: Aurora Serum | price: 78 | stock: 100" in parsed.text


def test_csv_parser_rejects_empty_file() -> None:
    with pytest.raises(ParserError):
        CsvParser().parse(b"", "empty.csv")


def test_pdf_parser_extracts_text_and_page_count() -> None:
    pipeline = IngestionPipeline()
    result = pipeline.run(make_pdf("Hello NUME Knowledge Base"), "brand.pdf")
    assert result.doc_type == "pdf"
    assert "Hello NUME Knowledge Base" in result.text
    assert result.page_count == 1
    assert len(result.chunks) == 1


def test_docx_parser_extracts_paragraphs() -> None:
    content = make_docx(["NUMÉ Brand Voice", "Warm, confident, science-led."])
    result = IngestionPipeline().run(content, "voice.docx")
    assert result.doc_type == "docx"
    assert "NUMÉ Brand Voice" in result.text
    assert "science-led" in result.text


def test_image_without_ocr_engine_fails_with_clear_message() -> None:
    from app.services.ingestion.ocr import NullOCREngine
    from app.services.ingestion.parsers import ImageParser
    import app.services.ingestion.parsers as parsers_mod

    # Force the null engine regardless of what's installed locally
    original = parsers_mod.get_ocr_engine
    parsers_mod.get_ocr_engine = lambda: NullOCREngine()
    try:
        with pytest.raises(ParserError, match="OCR"):
            ImageParser().parse(b"\x89PNG fake", "scan.png")
    finally:
        parsers_mod.get_ocr_engine = original


# --------------------------------------------------------------------------- #
# Pipeline
# --------------------------------------------------------------------------- #
def test_pipeline_rejects_empty_file() -> None:
    with pytest.raises(IngestionError):
        IngestionPipeline().run(b"", "empty.txt")


def test_pipeline_full_run_on_text() -> None:
    text = ("NUMÉ ingredient glossary. " * 200).encode("utf-8")
    result = IngestionPipeline(chunk_size=800, chunk_overlap=100).run(text, "glossary.txt")
    assert result.doc_type == "txt"
    assert result.word_count > 0
    assert result.char_count > 0
    assert result.excerpt
    assert len(result.chunks) > 1
