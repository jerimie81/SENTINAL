from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class Document:
    title: str
    content: str
    source_path: str | None = None
    id: str = ""
    created_at: datetime = datetime.now(timezone.utc)

    def __post_init__(self) -> None:
        if not self.id:
            object.__setattr__(self, "id", str(uuid4()))


@dataclass(frozen=True, slots=True)
class Chunk:
    document_id: str
    content: str
    index: int


@dataclass(frozen=True, slots=True)
class SearchResult:
    chunk: Chunk
    score: float
