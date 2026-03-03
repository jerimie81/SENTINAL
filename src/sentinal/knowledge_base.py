from __future__ import annotations

from dataclasses import dataclass, field

from .chunking import chunk_document
from .config import RetrievalConfig
from .embeddings import Embedder
from .index import VectorIndex
from .models import Document, SearchResult


@dataclass(slots=True)
class KnowledgeBase:
    embedder: Embedder
    config: RetrievalConfig = field(default_factory=RetrievalConfig)
    _documents: dict[str, Document] = field(default_factory=dict)
    _index: VectorIndex = field(default_factory=VectorIndex)

    def add_document(self, document: Document) -> int:
        self._documents[document.id] = document
        chunks = chunk_document(
            document,
            chunk_size=self.config.chunk_size,
            overlap=self.config.chunk_overlap,
        )
        for chunk in chunks:
            self._index.add(chunk, self.embedder.embed(chunk.content))
        return len(chunks)

    def search(self, query: str, top_k: int | None = None) -> list[SearchResult]:
        if self._index.size == 0:
            return []
        k = top_k if top_k is not None else self.config.top_k
        query_embedding = self.embedder.embed(query)
        return self._index.search(query_embedding, top_k=k)

    @property
    def document_count(self) -> int:
        return len(self._documents)
