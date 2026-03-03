"""In-memory + persistent vector/lexical index for SENTINAL.

Design
------
- Default embedder: HashEmbedder — guaranteed offline fallback, no deps.
- Persistence: numpy .npz for vectors, JSON for metadata sidecar.
- Search: cosine similarity over stored embeddings + optional TF-IDF
  lexical scoring (hybrid when both are available).

The index is intentionally simple and kept dependency-light for the
offline-first baseline.  Pluggable embedder support (Phase C1) is
reserved via the Embedder ABC.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from abc import ABC, abstractmethod
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from sentinal.errors import IndexError as SentinalIndexError
from sentinal.logging_utils import get_logger

log = get_logger("index")

# ---------------------------------------------------------------------------
# Embedder ABC + HashEmbedder fallback
# ---------------------------------------------------------------------------

class Embedder(ABC):
    """Abstract embedder interface."""

    DIM: int = 256

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Return a float vector for *text*."""

    @property
    def model_id(self) -> str:
        return self.__class__.__name__

    @property
    def model_version(self) -> str:
        return "0"


class HashEmbedder(Embedder):
    """Deterministic hash-based embedder — zero dependencies.

    Maps text to a 256-dim float vector via character n-gram hashing.
    Quality is low but the fallback guarantees offline operation.
    """

    DIM = 256

    def embed(self, text: str) -> List[float]:
        vec = [0.0] * self.DIM
        tokens = text.lower().split()
        if not tokens:
            return vec
        for tok in tokens:
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            idx = h % self.DIM
            vec[idx] += 1.0
        # L2 normalise
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

    @property
    def model_version(self) -> str:
        return "1"


# ---------------------------------------------------------------------------
# Simple TF-IDF lexical scorer (offline, no deps)
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"\w+")


def _tokenise(text: str) -> List[str]:
    return _TOKEN_RE.findall(text.lower())


class _LexicalIndex:
    """Inverted index with TF-IDF scoring."""

    def __init__(self) -> None:
        self._doc_tokens: Dict[str, List[str]] = {}   # chunk_id → tokens
        self._df: Dict[str, int] = defaultdict(int)   # term → doc freq

    def add(self, chunk_id: str, text: str) -> None:
        toks = _tokenise(text)
        self._doc_tokens[chunk_id] = toks
        for t in set(toks):
            self._df[t] += 1

    def remove(self, chunk_id: str) -> None:
        toks = self._doc_tokens.pop(chunk_id, [])
        for t in set(toks):
            self._df[t] = max(0, self._df[t] - 1)

    def score(self, query: str, chunk_id: str) -> float:
        """Return TF-IDF dot product score for query against chunk."""
        qtoks = _tokenise(query)
        dtoks = self._doc_tokens.get(chunk_id, [])
        if not dtoks:
            return 0.0
        n = len(self._doc_tokens)
        tf: Dict[str, float] = defaultdict(float)
        for t in dtoks:
            tf[t] += 1.0
        for t in tf:
            tf[t] /= len(dtoks)
        score = 0.0
        for qt in set(qtoks):
            df = self._df.get(qt, 0)
            if df == 0:
                continue
            idf = math.log((n + 1) / (df + 1)) + 1
            score += tf.get(qt, 0.0) * idf
        return score


# ---------------------------------------------------------------------------
# Core index
# ---------------------------------------------------------------------------

class VectorIndex:
    """Hybrid (vector + lexical) index over text chunks.

    Args:
        embedder: Embedder instance.  Defaults to HashEmbedder.
        index_dir: Directory for persistence files.
    """

    def __init__(
        self,
        embedder: Optional[Embedder] = None,
        index_dir: Optional[Path] = None,
    ) -> None:
        self._embedder = embedder or HashEmbedder()
        self._index_dir = Path(index_dir) if index_dir else None
        self._vectors: Dict[str, List[float]] = {}   # chunk_id → vector
        self._texts: Dict[str, str] = {}             # chunk_id → text
        self._meta: Dict[str, Dict] = {}             # chunk_id → extra meta
        self._lexical = _LexicalIndex()
        if self._index_dir:
            self._index_dir.mkdir(parents=True, exist_ok=True)
            self.load()

    # ------------------------------------------------------------------
    # Write path
    # ------------------------------------------------------------------

    def add(self, chunk_id: str, text: str, meta: Optional[Dict] = None) -> None:
        """Add or update a chunk in the index.

        Args:
            chunk_id: Unique chunk identifier.
            text:     Chunk content.
            meta:     Optional metadata dict (doc_id, source, etc.).
        """
        vec = self._embedder.embed(text)
        self._vectors[chunk_id] = vec
        self._texts[chunk_id] = text
        self._meta[chunk_id] = meta or {}
        self._lexical.add(chunk_id, text)

    def remove(self, chunk_id: str) -> None:
        """Remove a chunk from the index."""
        self._vectors.pop(chunk_id, None)
        self._texts.pop(chunk_id, None)
        self._meta.pop(chunk_id, None)
        self._lexical.remove(chunk_id)

    def remove_by_doc(self, doc_id: str) -> int:
        """Remove all chunks belonging to *doc_id*.  Returns count removed."""
        ids = [cid for cid, m in self._meta.items() if m.get("doc_id") == doc_id]
        for cid in ids:
            self.remove(cid)
        return len(ids)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        top_k: int = 5,
        alpha: float = 0.7,
    ) -> List[Tuple[str, float, Dict]]:
        """Search the index for chunks relevant to *query*.

        Args:
            query: Natural language query string.
            top_k: Number of results to return.
            alpha: Weight of vector score vs lexical score (0=lexical, 1=vector).

        Returns:
            List of (chunk_id, score, meta) tuples, descending by score.
        """
        if not self._vectors:
            return []

        q_vec = self._embedder.embed(query)
        results: List[Tuple[str, float]] = []
        for cid, vec in self._vectors.items():
            v_score = _cosine(q_vec, vec)
            l_score = self._lexical.score(query, cid)
            combined = alpha * v_score + (1 - alpha) * l_score
            results.append((cid, combined))

        results.sort(key=lambda x: x[1], reverse=True)
        return [
            (cid, score, self._meta.get(cid, {}))
            for cid, score in results[:top_k]
        ]

    def get_text(self, chunk_id: str) -> Optional[str]:
        """Return raw text for a chunk, or None."""
        return self._texts.get(chunk_id)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self) -> None:
        """Persist index to disk.

        Raises:
            SentinalIndexError: If no index_dir was configured.
        """
        if not self._index_dir:
            raise SentinalIndexError("No index_dir configured for persistence.")
        try:
            import numpy as np  # type: ignore
            ids = list(self._vectors.keys())
            matrix = np.array([self._vectors[i] for i in ids], dtype=np.float32)
            np.savez(self._index_dir / "vectors.npz", ids=ids, matrix=matrix)
        except ImportError:
            # Fallback: store as JSON (slower, larger)
            vec_path = self._index_dir / "vectors.json"
            vec_path.write_text(json.dumps(self._vectors))

        meta_path = self._index_dir / "meta.json"
        meta_path.write_text(
            json.dumps({"texts": self._texts, "meta": self._meta})
        )
        log.debug("Index saved to %s (%d chunks)", self._index_dir, len(self._vectors))

    def load(self) -> None:
        """Load index from disk if persistence files exist."""
        if not self._index_dir:
            return
        meta_path = self._index_dir / "meta.json"
        if not meta_path.exists():
            return
        try:
            data = json.loads(meta_path.read_text())
            self._texts = data.get("texts", {})
            self._meta = data.get("meta", {})
        except Exception as exc:
            raise SentinalIndexError(
                f"Index metadata corrupted at '{meta_path}': {exc}. "
                "Run 'sentinal doctor' for remediation options."
            ) from exc

        # Reload vectors
        npz_path = self._index_dir / "vectors.npz"
        json_path = self._index_dir / "vectors.json"
        if npz_path.exists():
            try:
                import numpy as np  # type: ignore
                data = np.load(npz_path, allow_pickle=False)
                ids = list(data["ids"])
                matrix = data["matrix"]
                self._vectors = {ids[i]: matrix[i].tolist() for i in range(len(ids))}
            except Exception as exc:
                raise SentinalIndexError(
                    f"Index vectors corrupted at '{npz_path}': {exc}."
                ) from exc
        elif json_path.exists():
            try:
                self._vectors = json.loads(json_path.read_text())
            except Exception as exc:
                raise SentinalIndexError(
                    f"Index vectors corrupted at '{json_path}': {exc}."
                ) from exc

        # Rebuild lexical index from loaded texts
        for cid, text in self._texts.items():
            self._lexical.add(cid, text)

        log.debug("Index loaded from %s (%d chunks)", self._index_dir, len(self._vectors))

    def integrity_check(self) -> List[str]:
        """Return a list of inconsistency descriptions, empty if healthy."""
        issues = []
        vec_ids = set(self._vectors.keys())
        text_ids = set(self._texts.keys())
        if vec_ids != text_ids:
            only_vec = vec_ids - text_ids
            only_text = text_ids - vec_ids
            if only_vec:
                issues.append(f"Vectors without text: {len(only_vec)} chunks")
            if only_text:
                issues.append(f"Texts without vectors: {len(only_text)} chunks")
        return issues

    def stats(self) -> Dict:
        return {
            "chunks": len(self._vectors),
            "embedder": self._embedder.model_id,
            "index_dir": str(self._index_dir) if self._index_dir else None,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cosine(a: List[float], b: List[float]) -> float:
    """Cosine similarity between two pre-normalised vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a)) or 1.0
    mag_b = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (mag_a * mag_b)
