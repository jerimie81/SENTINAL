"""Chunking strategies for SENTINAL.

Splits document text into overlapping chunks with deterministic IDs and
provenance mappings (chunk → original character offsets).

Strategy modes
--------------
- ``fixed_token``:  Split by approximate token count (word-based).
- ``sentence``:     Split on sentence boundaries, then merge up to limit.

All strategies produce stable, deterministic chunk IDs based on
(doc_id, chunk_index) so that re-ingestion is idempotent.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import List, Literal

from sentinal.errors import ChunkingError
from sentinal.logging_utils import get_logger

log = get_logger("chunker")

Strategy = Literal["fixed_token", "sentence"]


@dataclass
class Chunk:
    """A single text chunk with provenance metadata."""

    id: str            # Deterministic: sha256(doc_id + str(index))
    doc_id: str
    chunk_index: int
    content: str
    start_char: int    # Offset into original document text
    end_char: int
    token_count: int   # Approximate word-token count


def _make_chunk_id(doc_id: str, index: int) -> str:
    key = f"{doc_id}:{index}"
    return hashlib.sha256(key.encode()).hexdigest()


def _approx_tokens(text: str) -> int:
    """Approximate token count using whitespace splitting."""
    return len(text.split())


# ---------------------------------------------------------------------------
# Fixed-token strategy
# ---------------------------------------------------------------------------

def _split_fixed_token(
    text: str,
    doc_id: str,
    chunk_size: int,
    overlap: int,
) -> List[Chunk]:
    """Split *text* into overlapping fixed-token-count chunks.

    Args:
        text:        Full document text.
        doc_id:      Parent document ID.
        chunk_size:  Target token count per chunk.
        overlap:     Token overlap between consecutive chunks.

    Returns:
        Ordered list of Chunk objects.
    """
    words = text.split()
    if not words:
        return []

    chunks: List[Chunk] = []
    step = max(1, chunk_size - overlap)
    word_pos = 0  # running char offset tracker

    # Build a fast word → char-start index
    # We rebuild by scanning text once
    word_starts: List[int] = []
    pos = 0
    for w in words:
        idx = text.index(w, pos)
        word_starts.append(idx)
        pos = idx + len(w)

    i = 0
    chunk_index = 0
    while i < len(words):
        end = min(i + chunk_size, len(words))
        window_words = words[i:end]
        content = " ".join(window_words)
        start_char = word_starts[i]
        last_word_idx = end - 1
        end_char = word_starts[last_word_idx] + len(words[last_word_idx])

        chunks.append(
            Chunk(
                id=_make_chunk_id(doc_id, chunk_index),
                doc_id=doc_id,
                chunk_index=chunk_index,
                content=content,
                start_char=start_char,
                end_char=end_char,
                token_count=len(window_words),
            )
        )
        chunk_index += 1
        i += step

    return chunks


# ---------------------------------------------------------------------------
# Sentence strategy
# ---------------------------------------------------------------------------

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _split_sentences(text: str) -> List[tuple[str, int]]:
    """Split text into (sentence, start_char) pairs."""
    result: List[tuple[str, int]] = []
    pos = 0
    for sent in _SENTENCE_SPLIT.split(text):
        idx = text.index(sent, pos)
        result.append((sent.strip(), idx))
        pos = idx + len(sent)
    return result


def _split_sentence_strategy(
    text: str,
    doc_id: str,
    chunk_size: int,
    overlap: int,
) -> List[Chunk]:
    """Merge sentences into chunks up to *chunk_size* tokens.

    Overlap is implemented by re-including the last sentence(s) of the
    previous chunk up to *overlap* tokens.
    """
    sentences = _split_sentences(text)
    if not sentences:
        return []

    chunks: List[Chunk] = []
    chunk_index = 0
    i = 0

    while i < len(sentences):
        buf: List[str] = []
        buf_tokens = 0
        start_char = sentences[i][1]
        j = i
        while j < len(sentences):
            s, _ = sentences[j]
            t = _approx_tokens(s)
            if buf_tokens + t > chunk_size and buf:
                break
            buf.append(s)
            buf_tokens += t
            j += 1

        content = " ".join(buf)
        end_sent_idx = j - 1
        end_char = sentences[end_sent_idx][1] + len(sentences[end_sent_idx][0])

        chunks.append(
            Chunk(
                id=_make_chunk_id(doc_id, chunk_index),
                doc_id=doc_id,
                chunk_index=chunk_index,
                content=content,
                start_char=start_char,
                end_char=end_char,
                token_count=buf_tokens,
            )
        )
        chunk_index += 1

        # Advance, back-tracking by overlap tokens
        overlap_tokens = 0
        k = j - 1
        while k >= i and overlap_tokens < overlap:
            overlap_tokens += _approx_tokens(sentences[k][0])
            k -= 1
        i = max(k + 1, i + 1)  # guarantee forward progress

    return chunks


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def chunk_document(
    text: str,
    doc_id: str,
    strategy: Strategy = "fixed_token",
    chunk_size: int = 512,
    overlap: int = 64,
) -> List[Chunk]:
    """Split *text* into chunks using the given *strategy*.

    Args:
        text:        Full document text.
        doc_id:      Parent document ID (used for deterministic chunk IDs).
        strategy:    "fixed_token" or "sentence".
        chunk_size:  Target token count per chunk.
        overlap:     Token overlap between consecutive chunks.

    Returns:
        Ordered list of Chunk objects.  Empty list for empty input.

    Raises:
        ChunkingError: On invalid parameters.
    """
    if chunk_size < 32:
        raise ChunkingError(f"chunk_size must be >= 32, got {chunk_size}")
    if overlap < 0:
        raise ChunkingError(f"overlap must be >= 0, got {overlap}")
    if overlap >= chunk_size:
        raise ChunkingError(
            f"overlap ({overlap}) must be < chunk_size ({chunk_size})"
        )
    if not text.strip():
        return []

    if strategy == "fixed_token":
        result = _split_fixed_token(text, doc_id, chunk_size, overlap)
    elif strategy == "sentence":
        result = _split_sentence_strategy(text, doc_id, chunk_size, overlap)
    else:
        raise ChunkingError(
            f"Unknown strategy '{strategy}'. "
            "Choose from: 'fixed_token', 'sentence'."
        )

    log.debug(
        "Chunked doc_id=%s strategy=%s chunks=%d",
        doc_id, strategy, len(result),
    )
    return result
