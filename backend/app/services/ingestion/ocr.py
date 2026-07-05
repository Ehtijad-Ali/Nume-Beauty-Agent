"""OCR engine architecture for image-based documents.

Phase 2.1 prepares the architecture only: a pluggable :class:`OCREngine`
protocol with a Tesseract implementation that activates automatically when
the optional dependencies (``pytesseract`` + ``Pillow`` + the Tesseract
binary) are installed. Without them, image uploads are accepted and stored
but marked as failed to index with a clear message.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class OCREngine(Protocol):
    """Interface every OCR backend must implement."""

    name: str

    def is_available(self) -> bool:
        """Whether the engine can run in this environment."""
        ...

    def extract_text(self, image_bytes: bytes) -> str:
        """Return the text recognised in the given image bytes."""
        ...


class TesseractOCREngine:
    """OCR backed by Tesseract via the optional ``pytesseract`` package."""

    name = "tesseract"

    def is_available(self) -> bool:
        try:
            import pytesseract  # noqa: F401
            from PIL import Image  # noqa: F401
        except ImportError:
            return False
        try:
            import pytesseract

            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def extract_text(self, image_bytes: bytes) -> str:
        import io

        import pytesseract
        from PIL import Image

        with Image.open(io.BytesIO(image_bytes)) as image:
            return pytesseract.image_to_string(image)


class NullOCREngine:
    """Fallback used when no OCR backend is installed."""

    name = "none"

    def is_available(self) -> bool:
        return False

    def extract_text(self, image_bytes: bytes) -> str:
        raise RuntimeError(
            "No OCR engine is available. Install the optional OCR extras "
            "(pytesseract + Pillow + the Tesseract binary) to index images."
        )


_ENGINES: list[OCREngine] = [TesseractOCREngine()]


def get_ocr_engine() -> OCREngine:
    """Return the first available OCR engine, or the null engine."""
    for engine in _ENGINES:
        if engine.is_available():
            return engine
    return NullOCREngine()


def register_ocr_engine(engine: OCREngine) -> None:
    """Register a custom OCR backend (takes priority over built-ins)."""
    _ENGINES.insert(0, engine)
