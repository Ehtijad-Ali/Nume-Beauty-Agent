"""Context builder — Phase 2.3.

Turns ranked chunks into (a) the numbered context block injected into the
prompt and (b) the per-document source list used for citations.
"""

from __future__ import annotations

from typing import Any

from app.config.settings import get_settings


def build_context(chunks: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    """Assemble the context block and source citations.

    Returns ``(context_text, sources)``. Every chunk gets a citation number
    ``[n]`` used both in the context block and in the LLM's answer; sources
    aggregate the used chunks per document. Chunks that would exceed the
    context character budget are dropped (never truncated mid-sentence).
    """
    settings = get_settings()
    budget = settings.rag_max_context_chars

    parts: list[str] = []
    sources: list[dict[str, Any]] = []
    by_document: dict[str, dict[str, Any]] = {}
    used = 0
    citation = 0

    for chunk in chunks:
        header_bits = [chunk.get("title") or "Untitled document"]
        if chunk.get("page"):
            header_bits.append(f"p.{chunk['page']}")
        if chunk.get("category_name"):
            header_bits.append(chunk["category_name"])
        content = (chunk.get("content") or "").strip()
        block = f"[{citation + 1}] ({' — '.join(str(b) for b in header_bits)})\n{content}"
        if parts and used + len(block) > budget:
            continue
        citation += 1
        chunk["citation"] = citation
        parts.append(block)
        used += len(block)

        doc_id = str(chunk.get("document_id"))
        source = by_document.get(doc_id)
        if source is None:
            source = {
                "document_id": doc_id,
                "title": chunk.get("title"),
                "doc_type": chunk.get("doc_type"),
                "category_name": chunk.get("category_name"),
                "brand": chunk.get("brand"),
                "citations": [],
                "chunks_used": 0,
                "best_score": 0.0,
            }
            by_document[doc_id] = source
            sources.append(source)
        source["citations"].append(citation)
        source["chunks_used"] += 1
        source["best_score"] = max(source["best_score"], float(chunk.get("score") or 0.0))

    return "\n\n".join(parts), sources
