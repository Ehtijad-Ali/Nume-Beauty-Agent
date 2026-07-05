"""Text chunking — split normalised text into indexable segments.

Chunks respect paragraph boundaries where possible and overlap slightly so
context is not lost at the seams. No tokenisers or embeddings are used —
sizes are measured in characters.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

DEFAULT_CHUNK_SIZE = 1500  # characters
DEFAULT_CHUNK_OVERLAP = 200  # characters

# Smart per-doc-type profiles: (chunk_size, overlap). CSV rows are short and
# self-contained (no overlap needed); prose formats benefit from overlap.
CHUNK_PROFILES: dict[str, tuple[int, int]] = {
    "csv": (800, 0),
    "txt": (1200, 150),
    "md": (1200, 150),
    "image": (1200, 150),
    "pdf": (DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP),
    "docx": (DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP),
}


def chunk_profile(doc_type: str) -> tuple[int, int]:
    """Return the (size, overlap) profile for a document type."""
    return CHUNK_PROFILES.get(doc_type, (DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP))

_PARAGRAPH_SPLIT = re.compile(r"\n{2,}")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


@dataclass
class TextChunk:
    """One chunk of text with its position in the source document."""

    index: int
    content: str
    # Source location hints (e.g. {"page": 3}) carried into the vector index.
    metadata: dict | None = None


def chunk_text(
    text: str,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[TextChunk]:
    """Split text into chunks of roughly ``chunk_size`` characters.

    Paragraphs are packed together until the limit is reached; paragraphs
    longer than the limit are split on sentence boundaries (falling back to
    a hard split). Consecutive chunks share ``overlap`` trailing characters.
    """
    if not text or not text.strip():
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    overlap = max(0, min(overlap, chunk_size // 2))

    # Break the document into units no longer than chunk_size
    units: list[str] = []
    for paragraph in _PARAGRAPH_SPLIT.split(text):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        if len(paragraph) <= chunk_size:
            units.append(paragraph)
        else:
            units.extend(_split_long_text(paragraph, chunk_size))

    # Pack units into chunks
    chunks: list[str] = []
    current = ""
    for unit in units:
        candidate = f"{current}\n\n{unit}" if current else unit
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                chunks.append(current)
            # Seed the next chunk with the tail of the previous one
            tail = _overlap_tail(current, overlap)
            current = f"{tail}\n\n{unit}" if tail else unit
            # Guard: unit itself fits (ensured above), but tail may overflow
            if len(current) > chunk_size:
                current = unit
    if current:
        chunks.append(current)

    return [TextChunk(index=i, content=chunk) for i, chunk in enumerate(chunks)]


def _split_long_text(text: str, chunk_size: int) -> list[str]:
    """Split an over-long paragraph on sentences, then hard-wrap."""
    pieces: list[str] = []
    current = ""
    for sentence in _SENTENCE_END.split(text):
        if not sentence:
            continue
        if len(sentence) > chunk_size:
            if current:
                pieces.append(current)
                current = ""
            pieces.extend(
                sentence[i : i + chunk_size] for i in range(0, len(sentence), chunk_size)
            )
            continue
        candidate = f"{current} {sentence}".strip() if current else sentence
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            pieces.append(current)
            current = sentence
    if current:
        pieces.append(current)
    return pieces


def _overlap_tail(text: str, overlap: int) -> str:
    """Return the last ``overlap`` characters, starting at a word boundary."""
    if overlap <= 0 or not text:
        return ""
    tail = text[-overlap:]
    if " " in tail:
        tail = tail[tail.index(" ") + 1 :]
    return tail.strip()
