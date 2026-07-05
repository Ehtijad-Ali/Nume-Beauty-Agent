"""Text cleaning and normalisation utilities."""

from __future__ import annotations

import re
import unicodedata

# Control characters except \n and \t
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")
# Words split across lines with a hyphen: "market-\ning" -> "marketing"
_HYPHEN_BREAK = re.compile(r"(\w)-\n(\w)")
# 3+ consecutive newlines -> paragraph break
_MULTI_NEWLINE = re.compile(r"\n{3,}")
# Runs of spaces/tabs
_MULTI_SPACE = re.compile(r"[ \t]{2,}")

# Common "smart" punctuation to ASCII equivalents
_PUNCTUATION_MAP = str.maketrans(
    {
        "‘": "'",
        "’": "'",
        "“": '"',
        "”": '"',
        "–": "-",
        "—": "-",
        "…": "...",
        " ": " ",  # non-breaking space
        "​": "",  # zero-width space
        "﻿": "",  # BOM
    }
)


def clean_text(text: str) -> str:
    """Remove artifacts that commonly survive document extraction.

    Strips control characters, repairs hyphenated line breaks, collapses
    excessive whitespace, and trims trailing space on every line.
    """
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _CONTROL_CHARS.sub("", text)
    text = _HYPHEN_BREAK.sub(r"\1\2", text)
    text = _MULTI_SPACE.sub(" ", text)
    # Trim whitespace at line ends, drop lines that are only whitespace noise
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)
    text = _MULTI_NEWLINE.sub("\n\n", text)
    return text.strip()


def normalize_text(text: str) -> str:
    """Normalise unicode (NFKC) and standardise punctuation.

    Keeps the text human-readable while making it consistent for search
    and downstream indexing.
    """
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(_PUNCTUATION_MAP)
    return text


def clean_and_normalize(text: str) -> str:
    """Full cleaning pass: normalise unicode first, then clean artifacts."""
    return clean_text(normalize_text(text))


def word_count(text: str) -> int:
    """Count whitespace-separated words."""
    return len(text.split()) if text else 0


def make_excerpt(text: str, max_chars: int = 500) -> str:
    """Return a short single-paragraph excerpt for previews."""
    if not text:
        return ""
    flattened = re.sub(r"\s+", " ", text).strip()
    if len(flattened) <= max_chars:
        return flattened
    cut = flattened[:max_chars]
    # Avoid cutting mid-word
    if " " in cut:
        cut = cut[: cut.rfind(" ")]
    return cut + "…"
