"""Compatibility exports for source adapters."""

from .adapters_py import (
    BaseAdapter,
    DocumentRecord,
    MarkdownAdapter,
    PdfAdapter,
    TxtAdapter,
    get_adapter,
)

__all__ = [
    "BaseAdapter",
    "DocumentRecord",
    "MarkdownAdapter",
    "PdfAdapter",
    "TxtAdapter",
    "get_adapter",
]
