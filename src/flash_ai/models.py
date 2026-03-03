from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List
from uuid import uuid4


@dataclass(slots=True)
class Flashcard:
    question: str
    answer: str
    tags: List[str] = field(default_factory=list)


@dataclass(slots=True)
class Deck:
    title: str
    source_text: str
    cards: List[Flashcard]
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
