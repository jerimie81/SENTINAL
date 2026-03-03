"""Domain exception hierarchy for SENTINAL.

All public exceptions derive from SentinalError, allowing callers to
catch the entire domain with a single except clause if needed.
"""


class SentinalError(Exception):
    """Base class for all SENTINAL domain errors."""


class ConfigError(SentinalError):
    """Raised when configuration is invalid or missing required values."""


class IngestionError(SentinalError):
    """Raised when document ingestion fails (parse, I/O, format errors)."""


class IndexError(SentinalError):
    """Raised when index operations fail (build, search, corruption)."""


class ChunkingError(SentinalError):
    """Raised when a chunking strategy cannot process a document."""


class StorageError(SentinalError):
    """Raised on persistent storage read/write failures."""


class SearchError(SentinalError):
    """Raised when a search query cannot be executed."""


class QAError(SentinalError):
    """Raised when question-answering synthesis fails."""
