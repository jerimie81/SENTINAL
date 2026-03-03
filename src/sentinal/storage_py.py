"""Persistent SQLite metadata store for SENTINAL.

Stores document metadata (source, checksum, mime type, etc.) and
chunk records so that ingestion is idempotent and re-indexing can be
skipped for unchanged content.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Generator, List, Optional

from sentinal.errors import StorageError
from sentinal.logging_utils import get_logger

log = get_logger("storage")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id          TEXT PRIMARY KEY,
    source_uri  TEXT NOT NULL,
    checksum    TEXT NOT NULL,
    mime_type   TEXT,
    file_size   INTEGER,
    modified_at TEXT,
    ingested_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS chunks (
    id          TEXT PRIMARY KEY,
    doc_id      TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    start_char  INTEGER,
    end_char    INTEGER,
    token_count INTEGER,
    content     TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id);
CREATE INDEX IF NOT EXISTS idx_docs_checksum ON documents(checksum);
"""


class MetadataStore:
    """SQLite-backed store for document and chunk metadata.

    Args:
        db_path: Filesystem path for the SQLite database file.
    """

    def __init__(self, db_path: Path) -> None:
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._init()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def _init(self) -> None:
        """Create schema if the database is fresh."""
        try:
            conn = self._get_conn()
            conn.executescript(_SCHEMA)
            conn.commit()
            log.debug("MetadataStore initialised at %s", self._path)
        except sqlite3.Error as exc:
            raise StorageError(f"Failed to initialise metadata DB: {exc}") from exc

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            try:
                self._conn = sqlite3.connect(
                    self._path,
                    detect_types=sqlite3.PARSE_DECLTYPES,
                    check_same_thread=False,
                )
                self._conn.row_factory = sqlite3.Row
                self._conn.execute("PRAGMA journal_mode=WAL")
                self._conn.execute("PRAGMA foreign_keys=ON")
            except sqlite3.Error as exc:
                raise StorageError(
                    f"Cannot open metadata DB at '{self._path}': {exc}"
                ) from exc
        return self._conn

    def close(self) -> None:
        """Close the underlying connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    @contextmanager
    def _tx(self) -> Generator[sqlite3.Connection, None, None]:
        conn = self._get_conn()
        try:
            yield conn
            conn.commit()
        except sqlite3.Error as exc:
            conn.rollback()
            raise StorageError(f"Storage transaction failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Document operations
    # ------------------------------------------------------------------

    def document_exists(self, checksum: str) -> bool:
        """Return True if a document with *checksum* is already stored."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT 1 FROM documents WHERE checksum = ?", (checksum,)
        ).fetchone()
        return row is not None

    def upsert_document(self, doc: Dict) -> None:
        """Insert or replace a document record.

        Expected keys: id, source_uri, checksum, mime_type,
                        file_size, modified_at.
        """
        required = {"id", "source_uri", "checksum"}
        missing = required - doc.keys()
        if missing:
            raise StorageError(f"Document record missing keys: {missing}")
        with self._tx() as conn:
            conn.execute(
                """
                INSERT INTO documents
                    (id, source_uri, checksum, mime_type, file_size, modified_at)
                VALUES (:id, :source_uri, :checksum,
                        :mime_type, :file_size, :modified_at)
                ON CONFLICT(id) DO UPDATE SET
                    source_uri  = excluded.source_uri,
                    checksum    = excluded.checksum,
                    mime_type   = excluded.mime_type,
                    file_size   = excluded.file_size,
                    modified_at = excluded.modified_at,
                    ingested_at = datetime('now')
                """,
                {
                    "id": doc["id"],
                    "source_uri": doc["source_uri"],
                    "checksum": doc["checksum"],
                    "mime_type": doc.get("mime_type"),
                    "file_size": doc.get("file_size"),
                    "modified_at": doc.get("modified_at"),
                },
            )
        log.debug("Upserted document id=%s", doc["id"])

    def get_document(self, doc_id: str) -> Optional[Dict]:
        """Return a document record by id, or None."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM documents WHERE id = ?", (doc_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_documents(self) -> List[Dict]:
        """Return all document records."""
        conn = self._get_conn()
        return [dict(r) for r in conn.execute("SELECT * FROM documents").fetchall()]

    def delete_document(self, doc_id: str) -> None:
        """Delete a document and all its chunks (cascaded)."""
        with self._tx() as conn:
            conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))

    # ------------------------------------------------------------------
    # Chunk operations
    # ------------------------------------------------------------------

    def upsert_chunks(self, chunks: List[Dict]) -> None:
        """Bulk-insert or replace chunk records.

        Each dict needs: id, doc_id, chunk_index, content.
        Optional: start_char, end_char, token_count.
        """
        if not chunks:
            return
        with self._tx() as conn:
            conn.executemany(
                """
                INSERT INTO chunks
                    (id, doc_id, chunk_index, start_char, end_char,
                     token_count, content)
                VALUES (:id, :doc_id, :chunk_index, :start_char, :end_char,
                        :token_count, :content)
                ON CONFLICT(id) DO UPDATE SET
                    content     = excluded.content,
                    start_char  = excluded.start_char,
                    end_char    = excluded.end_char,
                    token_count = excluded.token_count
                """,
                [
                    {
                        "id": c["id"],
                        "doc_id": c["doc_id"],
                        "chunk_index": c["chunk_index"],
                        "start_char": c.get("start_char"),
                        "end_char": c.get("end_char"),
                        "token_count": c.get("token_count"),
                        "content": c["content"],
                    }
                    for c in chunks
                ],
            )

    def get_chunks_for_doc(self, doc_id: str) -> List[Dict]:
        """Return all chunks for a document, ordered by chunk_index."""
        conn = self._get_conn()
        return [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM chunks WHERE doc_id = ? ORDER BY chunk_index",
                (doc_id,),
            ).fetchall()
        ]

    def get_chunk(self, chunk_id: str) -> Optional[Dict]:
        """Return a single chunk record by id, or None."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM chunks WHERE id = ?", (chunk_id,)
        ).fetchone()
        return dict(row) if row else None

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self) -> Dict:
        """Return basic counts for the doctor/stats command."""
        conn = self._get_conn()
        doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        chunk_count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        return {"documents": doc_count, "chunks": chunk_count, "db_path": str(self._path)}
