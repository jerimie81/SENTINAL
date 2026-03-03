from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SentinalPaths:
    """Filesystem layout for portable/offline deployments."""

    root: Path
    documents_dir: Path
    state_dir: Path

    @classmethod
    def from_root(cls, root: Path) -> "SentinalPaths":
        root = root.resolve()
        return cls(
            root=root,
            documents_dir=root / "documents",
            state_dir=root / ".sentinal",
        )

    def ensure(self) -> None:
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True, slots=True)
class RetrievalConfig:
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k: int = 4
