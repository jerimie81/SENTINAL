from __future__ import annotations

from dataclasses import dataclass, field

from .models import Chunk, SearchResult


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


@dataclass(slots=True)
class VectorIndex:
    _entries: list[tuple[Chunk, list[float]]] = field(default_factory=list)

    def add(self, chunk: Chunk, embedding: list[float]) -> None:
        self._entries.append((chunk, embedding))

    def search(self, query_embedding: list[float], top_k: int) -> list[SearchResult]:
        ranked = [
            SearchResult(chunk=chunk, score=_dot(query_embedding, emb))
            for chunk, emb in self._entries
        ]
        ranked.sort(key=lambda x: x.score, reverse=True)
        return ranked[:top_k]

    @property
    def size(self) -> int:
        return len(self._entries)
