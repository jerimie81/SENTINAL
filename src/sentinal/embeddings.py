from __future__ import annotations

import hashlib
import math
from typing import Protocol


class Embedder(Protocol):
    def embed(self, text: str) -> list[float]:
        ...


class HashEmbedder:
    """Deterministic offline embedder for bootstrap environments.

    Produces stable vectors without external dependencies or network access.
    """

    def __init__(self, dimensions: int = 64) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be > 0")
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        if not text.strip():
            return [0.0] * self.dimensions

        vector = [0.0] * self.dimensions
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:2], "big") % self.dimensions
            val = int.from_bytes(digest[2:4], "big") / 65535.0
            vector[idx] += val

        norm = math.sqrt(sum(v * v for v in vector))
        if norm == 0:
            return vector
        return [v / norm for v in vector]
