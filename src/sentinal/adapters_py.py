"""Source adapters for document ingestion.

Each adapter reads a file and returns a normalised DocumentRecord
containing extracted text plus metadata. New formats are added by
subclassing BaseAdapter and registering in ADAPTER_REGISTRY.
"""

from __future__ import annotations

import hashlib
import mimetypes
import unicodedata
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Type

from sentinal.errors import IngestionError
from sentinal.logging_utils import get_logger

log = get_logger("adapters")


# ---------------------------------------------------------------------------
# Document record
# ---------------------------------------------------------------------------

@dataclass
class DocumentRecord:
    """Normalised output from an ingestion adapter."""

    id: str                    # Deterministic: sha256 of source_uri
    source_uri: str            # Absolute file path as string
    checksum: str              # sha256 of raw file content
    text: str                  # Extracted, normalised plain text
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    modified_at: Optional[str] = None
    extra: Dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Base adapter
# ---------------------------------------------------------------------------

class BaseAdapter(ABC):
    """Abstract document source adapter.

    Subclasses implement _extract_text(path) and declare SUPPORTED_SUFFIXES.
    """

    SUPPORTED_SUFFIXES: tuple[str, ...] = ()

    @abstractmethod
    def _extract_text(self, path: Path) -> str:
        """Extract and return raw text from *path*."""

    def load(self, path: Path) -> DocumentRecord:
        """Load *path* and return a normalised DocumentRecord.

        Args:
            path: Absolute or relative filesystem path.

        Returns:
            DocumentRecord with text and metadata populated.

        Raises:
            IngestionError: If the file cannot be read or parsed.
        """
        path = path.resolve()
        if not path.exists():
            raise IngestionError(f"File not found: {path}")
        if not path.is_file():
            raise IngestionError(f"Path is not a file: {path}")

        try:
            raw_bytes = path.read_bytes()
        except OSError as exc:
            raise IngestionError(f"Cannot read '{path}': {exc}") from exc

        checksum = hashlib.sha256(raw_bytes).hexdigest()
        doc_id = hashlib.sha256(str(path).encode()).hexdigest()

        try:
            raw_text = self._extract_text(path)
        except IngestionError:
            raise
        except Exception as exc:
            raise IngestionError(
                f"Extraction failed for '{path}': {exc}"
            ) from exc

        text = _normalise_text(raw_text)

        stat = path.stat()
        mime, _ = mimetypes.guess_type(str(path))
        modified_at = datetime.fromtimestamp(
            stat.st_mtime, tz=timezone.utc
        ).isoformat()

        log.debug("Loaded document id=%s path=%s chars=%d", doc_id, path, len(text))
        return DocumentRecord(
            id=doc_id,
            source_uri=str(path),
            checksum=checksum,
            text=text,
            mime_type=mime,
            file_size=stat.st_size,
            modified_at=modified_at,
        )


# ---------------------------------------------------------------------------
# Text normalisation
# ---------------------------------------------------------------------------

def _normalise_text(text: str) -> str:
    """Apply unicode normalisation and whitespace cleanup."""
    # NFC normalisation — consistent codepoint representation
    text = unicodedata.normalize("NFC", text)
    # Replace non-breaking spaces, zero-width chars, etc.
    text = text.replace("\u00a0", " ").replace("\u200b", "")
    # Collapse runs of spaces (not newlines) to single space
    import re
    text = re.sub(r"[ \t]+", " ", text)
    # Collapse 3+ consecutive blank lines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Concrete adapters
# ---------------------------------------------------------------------------

class TxtAdapter(BaseAdapter):
    """Plain-text file adapter (.txt, .text)."""

    SUPPORTED_SUFFIXES = (".txt", ".text")

    def _extract_text(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise IngestionError(str(exc)) from exc


class MarkdownAdapter(BaseAdapter):
    """Markdown file adapter (.md, .markdown).

    Returns raw markdown text; structure hints (headings) are preserved.
    """

    SUPPORTED_SUFFIXES = (".md", ".markdown")

    def _extract_text(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise IngestionError(str(exc)) from exc


class PdfAdapter(BaseAdapter):
    """PDF adapter (.pdf) — requires pypdf (optional dependency)."""

    SUPPORTED_SUFFIXES = (".pdf",)

    def _extract_text(self, path: Path) -> str:
        try:
            import pypdf  # type: ignore
        except ImportError:
            raise IngestionError(
                "PDF ingestion requires 'pypdf'. "
                "Install it with: pip install pypdf"
            )
        try:
            reader = pypdf.PdfReader(str(path))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n\n".join(pages)
        except Exception as exc:
            raise IngestionError(f"pypdf failed on '{path}': {exc}") from exc


# ---------------------------------------------------------------------------
# Adapter registry
# ---------------------------------------------------------------------------

ADAPTER_REGISTRY: Dict[str, Type[BaseAdapter]] = {}

for _cls in (TxtAdapter, MarkdownAdapter, PdfAdapter):
    for _ext in _cls.SUPPORTED_SUFFIXES:
        ADAPTER_REGISTRY[_ext] = _cls


def get_adapter(path: Path) -> BaseAdapter:
    """Return the appropriate adapter for *path* based on file extension.

    Raises:
        IngestionError: If the file extension has no registered adapter.
    """
    ext = path.suffix.lower()
    cls = ADAPTER_REGISTRY.get(ext)
    if cls is None:
        supported = sorted(ADAPTER_REGISTRY.keys())
        raise IngestionError(
            f"No adapter for '{ext}' files. "
            f"Supported formats: {supported}"
        )
    return cls()
