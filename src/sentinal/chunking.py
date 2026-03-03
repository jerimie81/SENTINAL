from __future__ import annotations

from .models import Chunk, Document


def chunk_document(document: Document, chunk_size: int, overlap: int) -> list[Chunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if overlap < 0:
        raise ValueError("overlap must be >= 0")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    words = document.content.split()
    if not words:
        return []

    chunks: list[Chunk] = []
    start = 0
    i = 0
    step = chunk_size - overlap
    while start < len(words):
        end = min(len(words), start + chunk_size)
        content = " ".join(words[start:end])
        chunks.append(Chunk(document_id=document.id, content=content, index=i))
        i += 1
        start += step

    return chunks
