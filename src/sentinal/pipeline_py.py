"""High-level ingest → index → search → ask pipeline for SENTINAL."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

from sentinal.adapters import get_adapter
from sentinal.chunker import Chunk, Strategy, chunk_document
from sentinal.config import SentinalConfig
from sentinal.errors import IngestionError, QAError
from sentinal.index import Embedder, VectorIndex
from sentinal.logging_utils import get_logger, timed_log
from sentinal.storage import MetadataStore

log = get_logger("pipeline")


class Pipeline:
    """Orchestrates the full SENTINAL workflow.

    Args:
        config:   Validated SentinalConfig.
        embedder: Optional custom embedder (default: HashEmbedder).
    """

    def __init__(
        self,
        config: SentinalConfig,
        embedder: Optional[Embedder] = None,
    ) -> None:
        self.config = config
        config.data_dir.mkdir(parents=True, exist_ok=True)
        self.store = MetadataStore(config.db_path)
        self.index = VectorIndex(
            embedder=embedder,
            index_dir=config.index_path,
        )

    # ------------------------------------------------------------------
    # Ingest
    # ------------------------------------------------------------------

    def ingest(
        self,
        path: Path,
        force: bool = False,
        strategy: Strategy = "fixed_token",
    ) -> Dict:
        """Ingest a document file into the index.

        Skips ingestion if the document checksum is unchanged (idempotent)
        unless *force* is True.

        Args:
            path:     Path to the document file.
            force:    Re-ingest even if checksum matches.
            strategy: Chunking strategy ("fixed_token" or "sentence").

        Returns:
            Dict with keys: doc_id, skipped, chunk_count, source_uri.

        Raises:
            IngestionError: On file read or parse failure.
        """
        path = Path(path)
        adapter = get_adapter(path)

        with timed_log(log, logging.INFO, "Ingested document", operation="ingest"):
            doc = adapter.load(path)

            if not force and self.store.document_exists(doc.checksum):
                log.info("Skipping unchanged document: %s", path)
                return {
                    "doc_id": doc.id,
                    "skipped": True,
                    "chunk_count": 0,
                    "source_uri": doc.source_uri,
                }

            chunks: List[Chunk] = chunk_document(
                text=doc.text,
                doc_id=doc.id,
                strategy=strategy,
                chunk_size=self.config.chunk_size,
                overlap=self.config.chunk_overlap,
            )

            # Persist metadata
            self.store.upsert_document({
                "id": doc.id,
                "source_uri": doc.source_uri,
                "checksum": doc.checksum,
                "mime_type": doc.mime_type,
                "file_size": doc.file_size,
                "modified_at": doc.modified_at,
            })
            self.store.upsert_chunks([
                {
                    "id": c.id,
                    "doc_id": c.doc_id,
                    "chunk_index": c.chunk_index,
                    "start_char": c.start_char,
                    "end_char": c.end_char,
                    "token_count": c.token_count,
                    "content": c.content,
                }
                for c in chunks
            ])

            # Clear old index entries for this doc, add new ones
            self.index.remove_by_doc(doc.id)
            for c in chunks:
                self.index.add(
                    chunk_id=c.id,
                    text=c.content,
                    meta={
                        "doc_id": doc.id,
                        "source_uri": doc.source_uri,
                        "chunk_index": c.chunk_index,
                        "start_char": c.start_char,
                        "end_char": c.end_char,
                    },
                )

            self.index.save()

        return {
            "doc_id": doc.id,
            "skipped": False,
            "chunk_count": len(chunks),
            "source_uri": doc.source_uri,
        }

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query: str, top_k: Optional[int] = None) -> List[Dict]:
        """Search the index for chunks relevant to *query*.

        Args:
            query: Natural language query string.
            top_k: Max results.  Defaults to config.max_results.

        Returns:
            List of result dicts with keys: chunk_id, score, text, meta.
        """
        k = top_k or self.config.max_results
        raw = self.index.search(query, top_k=k)
        results = []
        for chunk_id, score, meta in raw:
            text = self.index.get_text(chunk_id) or ""
            results.append({
                "chunk_id": chunk_id,
                "score": round(score, 4),
                "text": text,
                "meta": meta,
            })
        return results

    # ------------------------------------------------------------------
    # Ask
    # ------------------------------------------------------------------

    def ask(self, question: str, top_k: Optional[int] = None) -> Dict:
        """Answer *question* using retrieved context chunks.

        The answer synthesiser in this baseline is template-driven and
        clearly separates grounded facts from uncertainty signals.

        Args:
            question: User question string.
            top_k:    Number of context chunks to retrieve.

        Returns:
            Dict with keys: answer, sources, grounded.
        """
        results = self.search(question, top_k=top_k or self.config.max_results)
        if not results:
            return {
                "answer": (
                    "No relevant content found in the knowledge base. "
                    "Please ingest documents first."
                ),
                "sources": [],
                "grounded": False,
            }

        context_parts = []
        sources = []
        for i, r in enumerate(results, 1):
            snippet = r["text"][:600].replace("\n", " ")
            context_parts.append(f"[{i}] {snippet}")
            sources.append({
                "chunk_id": r["chunk_id"],
                "score": r["score"],
                "source_uri": r["meta"].get("source_uri", "unknown"),
                "chunk_index": r["meta"].get("chunk_index"),
            })

        context = "\n\n".join(context_parts)
        answer = _synthesise(question, context, results)

        return {
            "answer": answer,
            "sources": sources,
            "grounded": True,
        }

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self) -> Dict:
        """Return combined statistics from storage and index."""
        return {
            "storage": self.store.stats(),
            "index": self.index.stats(),
        }


# ---------------------------------------------------------------------------
# Simple template-driven answer synthesis (offline, no LLM required)
# ---------------------------------------------------------------------------

def _synthesise(question: str, context: str, results: List[Dict]) -> str:
    """Produce a grounded answer from retrieved context.

    In baseline mode this concatenates the top chunk with a clear
    attribution header.  The QA synthesis upgrade (Phase D1) replaces this.
    """
    top = results[0]
    source = top["meta"].get("source_uri", "unknown document")
    score = top["score"]

    lines = [
        f"Based on the available knowledge base (top relevance score: {score}):\n",
        top["text"][:1200],
        f"\n\n— Source: {source}",
    ]

    if len(results) > 1:
        lines.append(
            f"\n\nAdditional context found in {len(results) - 1} more chunk(s). "
            "Use `search` for the full ranked list."
        )

    if score < 0.1:
        lines.append(
            "\n\n⚠ Low confidence: retrieved content may not directly answer "
            "this question."
        )

    return "".join(lines)
