"""SENTINAL test suite — unit + integration tests for the sprint.

Run with:
    pytest tests/test_sentinal.py -v
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_dir():
    d = Path(tempfile.mkdtemp())
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def sample_txt(tmp_dir):
    p = tmp_dir / "sample.txt"
    p.write_text(
        "SENTINAL is an offline-first knowledge system.\n"
        "It supports document ingestion and question answering.\n"
        "Chunking strategies include fixed_token and sentence modes.",
        encoding="utf-8",
    )
    return p


@pytest.fixture
def sample_md(tmp_dir):
    p = tmp_dir / "sample.md"
    p.write_text(
        "# SENTINAL Overview\n\n"
        "SENTINAL builds a local AI knowledge base.\n\n"
        "## Features\n\n"
        "- Offline-first operation\n"
        "- Deterministic chunking\n"
        "- Hybrid retrieval\n",
        encoding="utf-8",
    )
    return p


@pytest.fixture
def config(tmp_dir):
    from sentinal.config import SentinalConfig
    return SentinalConfig(
        profile="dev",
        data_dir=tmp_dir / ".sentinal",
        chunk_size=64,
        chunk_overlap=8,
        max_results=5,
    )


# ===========================================================================
# errors.py
# ===========================================================================

class TestErrors:
    def test_hierarchy(self):
        from sentinal.errors import (
            ChunkingError, ConfigError, IndexError, IngestionError,
            QAError, SearchError, SentinalError, StorageError,
        )
        for cls in (ConfigError, IngestionError, IndexError,
                    ChunkingError, StorageError, SearchError, QAError):
            assert issubclass(cls, SentinalError)

    def test_raise_and_catch(self):
        from sentinal.errors import ConfigError, SentinalError
        with pytest.raises(SentinalError):
            raise ConfigError("bad config")


# ===========================================================================
# config.py
# ===========================================================================

class TestConfig:
    def test_defaults(self):
        from sentinal.config import SentinalConfig
        cfg = SentinalConfig(data_dir=Path("/tmp/test_sentinal_defaults"))
        assert cfg.profile == "dev"
        assert cfg.chunk_size == 512
        assert cfg.offline is True

    def test_invalid_profile(self):
        from sentinal.config import SentinalConfig
        from sentinal.errors import ConfigError
        with pytest.raises(ConfigError, match="Invalid profile"):
            SentinalConfig(profile="fantasy")  # type: ignore

    def test_invalid_chunk_size(self):
        from sentinal.config import SentinalConfig
        from sentinal.errors import ConfigError
        with pytest.raises(ConfigError, match="chunk_size"):
            SentinalConfig(chunk_size=10)

    def test_overlap_gte_chunk_size(self):
        from sentinal.config import SentinalConfig
        from sentinal.errors import ConfigError
        with pytest.raises(ConfigError, match="chunk_overlap"):
            SentinalConfig(chunk_size=64, chunk_overlap=64)

    def test_load_config_profile_defaults(self, monkeypatch, tmp_dir):
        from sentinal.config import load_config
        monkeypatch.delenv("SENTINAL_PROFILE", raising=False)
        cfg = load_config(profile="edge_lowmem")
        assert cfg.chunk_size == 256
        assert cfg.max_results == 5

    def test_env_override(self, monkeypatch):
        from sentinal.config import load_config
        monkeypatch.setenv("SENTINAL_CHUNK_SIZE", "128")
        monkeypatch.setenv("SENTINAL_LOG_LEVEL", "WARNING")
        cfg = load_config(profile="dev")
        assert cfg.chunk_size == 128
        assert cfg.log_level == "WARNING"

    def test_env_bad_int(self, monkeypatch):
        from sentinal.config import load_config
        from sentinal.errors import ConfigError
        monkeypatch.setenv("SENTINAL_CHUNK_SIZE", "notanint")
        with pytest.raises(ConfigError, match="integer"):
            load_config(profile="dev")

    def test_derived_paths(self, tmp_dir):
        from sentinal.config import SentinalConfig
        cfg = SentinalConfig(data_dir=tmp_dir / "data")
        assert cfg.db_path == tmp_dir / "data" / "metadata.db"
        assert cfg.index_path == tmp_dir / "data" / "index"


# ===========================================================================
# logging_utils.py
# ===========================================================================

class TestLogging:
    def test_redact_sensitive_keys(self):
        from sentinal.logging_utils import _redact_dict
        data = {"username": "alice", "password": "s3cret", "token": "abc123"}
        redacted = _redact_dict(data)
        assert redacted["username"] == "alice"
        assert redacted["password"] == "[REDACTED]"
        assert redacted["token"] == "[REDACTED]"

    def test_redact_case_insensitive(self):
        from sentinal.logging_utils import _redact_value
        assert _redact_value("API_KEY", "xyz") == "[REDACTED]"
        assert _redact_value("Secret", "xyz") == "[REDACTED]"

    def test_non_sensitive_passthrough(self):
        from sentinal.logging_utils import _redact_value
        assert _redact_value("chunk_size", 512) == 512

    def test_configure_logging_runs(self):
        from sentinal.logging_utils import configure_logging
        configure_logging("DEBUG", "human")
        configure_logging("INFO", "json")


# ===========================================================================
# adapters.py
# ===========================================================================

class TestAdapters:
    def test_txt_adapter(self, sample_txt):
        from sentinal.adapters import TxtAdapter
        rec = TxtAdapter().load(sample_txt)
        assert "SENTINAL" in rec.text
        assert rec.checksum
        assert rec.mime_type == "text/plain"

    def test_md_adapter(self, sample_md):
        from sentinal.adapters import MarkdownAdapter
        rec = MarkdownAdapter().load(sample_md)
        assert "SENTINAL" in rec.text

    def test_missing_file(self, tmp_dir):
        from sentinal.adapters import TxtAdapter
        from sentinal.errors import IngestionError
        with pytest.raises(IngestionError, match="not found"):
            TxtAdapter().load(tmp_dir / "ghost.txt")

    def test_unsupported_extension(self, tmp_dir):
        from sentinal.adapters import get_adapter
        from sentinal.errors import IngestionError
        p = tmp_dir / "file.xyz"
        p.write_text("hello")
        with pytest.raises(IngestionError, match="No adapter"):
            get_adapter(p)

    def test_deterministic_id(self, sample_txt):
        from sentinal.adapters import TxtAdapter
        r1 = TxtAdapter().load(sample_txt)
        r2 = TxtAdapter().load(sample_txt)
        assert r1.id == r2.id
        assert r1.checksum == r2.checksum

    def test_normalisation_applied(self, tmp_dir):
        from sentinal.adapters import TxtAdapter
        p = tmp_dir / "dirty.txt"
        p.write_bytes("hello\u00a0world\u200b  extra  spaces".encode("utf-8"))
        rec = TxtAdapter().load(p)
        assert "\u00a0" not in rec.text
        assert "\u200b" not in rec.text
        assert "  " not in rec.text  # collapsed


# ===========================================================================
# chunker.py
# ===========================================================================

class TestChunker:
    LONG_TEXT = " ".join([f"word{i}" for i in range(300)])

    def test_fixed_token_basic(self):
        from sentinal.chunker import chunk_document
        chunks = chunk_document(self.LONG_TEXT, "doc1", "fixed_token", 50, 10)
        assert len(chunks) > 1
        assert all(c.doc_id == "doc1" for c in chunks)

    def test_fixed_token_deterministic(self):
        from sentinal.chunker import chunk_document
        c1 = chunk_document(self.LONG_TEXT, "doc1", "fixed_token", 50, 10)
        c2 = chunk_document(self.LONG_TEXT, "doc1", "fixed_token", 50, 10)
        assert [c.id for c in c1] == [c.id for c in c2]

    def test_sentence_strategy(self):
        from sentinal.chunker import chunk_document
        text = "Hello world. This is a test. Another sentence here."
        chunks = chunk_document(text, "doc1", "sentence", 32, 4)
        assert len(chunks) >= 1

    def test_empty_text(self):
        from sentinal.chunker import chunk_document
        assert chunk_document("", "doc1") == []

    def test_invalid_overlap(self):
        from sentinal.chunker import chunk_document
        from sentinal.errors import ChunkingError
        with pytest.raises(ChunkingError, match="overlap"):
            chunk_document("some text", "doc1", "fixed_token", 64, 64)

    def test_unknown_strategy(self):
        from sentinal.chunker import chunk_document
        from sentinal.errors import ChunkingError
        with pytest.raises(ChunkingError, match="Unknown strategy"):
            chunk_document("some text", "doc1", "bogus", 64, 8)  # type: ignore

    def test_chunk_ids_unique(self):
        from sentinal.chunker import chunk_document
        chunks = chunk_document(self.LONG_TEXT, "doc1", "fixed_token", 50, 0)
        ids = [c.id for c in chunks]
        assert len(ids) == len(set(ids))

    def test_provenance_offsets(self):
        from sentinal.chunker import chunk_document
        text = "alpha beta gamma delta epsilon"
        chunks = chunk_document(text, "doc1", "fixed_token", 3, 0)
        for c in chunks:
            # Reconstructed slice should match stored content (modulo spaces)
            sliced = text[c.start_char:c.end_char]
            assert sliced.strip() == c.content.strip()


# ===========================================================================
# storage.py
# ===========================================================================

class TestStorage:
    def test_upsert_and_get_document(self, tmp_dir):
        from sentinal.storage import MetadataStore
        store = MetadataStore(tmp_dir / "meta.db")
        doc = {
            "id": "doc1",
            "source_uri": "/tmp/test.txt",
            "checksum": "abc123",
            "mime_type": "text/plain",
            "file_size": 100,
            "modified_at": "2024-01-01T00:00:00+00:00",
        }
        store.upsert_document(doc)
        result = store.get_document("doc1")
        assert result["id"] == "doc1"
        assert result["checksum"] == "abc123"

    def test_document_exists_by_checksum(self, tmp_dir):
        from sentinal.storage import MetadataStore
        store = MetadataStore(tmp_dir / "meta.db")
        store.upsert_document({
            "id": "doc2", "source_uri": "/f", "checksum": "zzz",
        })
        assert store.document_exists("zzz")
        assert not store.document_exists("nope")

    def test_upsert_and_get_chunks(self, tmp_dir):
        from sentinal.storage import MetadataStore
        store = MetadataStore(tmp_dir / "meta.db")
        store.upsert_document({
            "id": "doc3", "source_uri": "/f", "checksum": "ccc",
        })
        chunks = [
            {"id": f"chunk{i}", "doc_id": "doc3", "chunk_index": i, "content": f"text{i}"}
            for i in range(3)
        ]
        store.upsert_chunks(chunks)
        loaded = store.get_chunks_for_doc("doc3")
        assert len(loaded) == 3
        assert loaded[0]["chunk_index"] == 0

    def test_delete_document_cascades(self, tmp_dir):
        from sentinal.storage import MetadataStore
        store = MetadataStore(tmp_dir / "meta.db")
        store.upsert_document({"id": "d", "source_uri": "/f", "checksum": "x"})
        store.upsert_chunks([{"id": "c1", "doc_id": "d", "chunk_index": 0, "content": "hi"}])
        store.delete_document("d")
        assert store.get_document("d") is None
        assert store.get_chunks_for_doc("d") == []

    def test_stats(self, tmp_dir):
        from sentinal.storage import MetadataStore
        store = MetadataStore(tmp_dir / "meta.db")
        s = store.stats()
        assert "documents" in s
        assert "chunks" in s


# ===========================================================================
# index.py
# ===========================================================================

class TestIndex:
    def test_add_and_search(self):
        from sentinal.index import VectorIndex
        idx = VectorIndex()
        idx.add("c1", "SENTINAL offline AI knowledge", {"doc_id": "d1"})
        idx.add("c2", "python programming tutorial", {"doc_id": "d2"})
        results = idx.search("offline knowledge system", top_k=2)
        assert results[0][0] == "c1"

    def test_remove_by_doc(self):
        from sentinal.index import VectorIndex
        idx = VectorIndex()
        idx.add("c1", "text", {"doc_id": "d1"})
        idx.add("c2", "text", {"doc_id": "d1"})
        idx.add("c3", "text", {"doc_id": "d2"})
        n = idx.remove_by_doc("d1")
        assert n == 2
        assert idx.search("text", top_k=10)[0][0] == "c3"

    def test_persistence(self, tmp_dir):
        from sentinal.index import VectorIndex
        p = tmp_dir / "index"
        idx = VectorIndex(index_dir=p)
        idx.add("c1", "hello world", {"doc_id": "d1"})
        idx.save()

        idx2 = VectorIndex(index_dir=p)
        assert idx2.get_text("c1") == "hello world"

    def test_integrity_check_healthy(self):
        from sentinal.index import VectorIndex
        idx = VectorIndex()
        idx.add("c1", "text", {})
        assert idx.integrity_check() == []

    def test_integrity_check_detects_mismatch(self):
        from sentinal.index import VectorIndex
        idx = VectorIndex()
        idx.add("c1", "text", {})
        del idx._texts["c1"]          # Simulate corruption
        issues = idx.integrity_check()
        assert len(issues) > 0

    def test_empty_search(self):
        from sentinal.index import VectorIndex
        idx = VectorIndex()
        assert idx.search("anything") == []

    def test_hash_embedder_deterministic(self):
        from sentinal.index import HashEmbedder
        e = HashEmbedder()
        v1 = e.embed("hello world")
        v2 = e.embed("hello world")
        assert v1 == v2

    def test_hash_embedder_different_texts(self):
        from sentinal.index import HashEmbedder
        e = HashEmbedder()
        v1 = e.embed("hello world")
        v2 = e.embed("completely different text")
        assert v1 != v2


# ===========================================================================
# Integration: ingest → search → ask
# ===========================================================================

class TestIntegration:
    def test_ingest_search_ask(self, tmp_dir, sample_txt, config):
        from sentinal.pipeline import Pipeline
        pipeline = Pipeline(config)

        # Ingest
        result = pipeline.ingest(sample_txt)
        assert not result["skipped"]
        assert result["chunk_count"] > 0

        # Idempotent re-ingest
        result2 = pipeline.ingest(sample_txt)
        assert result2["skipped"]

        # Force re-ingest
        result3 = pipeline.ingest(sample_txt, force=True)
        assert not result3["skipped"]

        # Search
        hits = pipeline.search("offline knowledge system")
        assert len(hits) > 0
        assert "score" in hits[0]

        # Ask
        qa = pipeline.ask("What is SENTINAL?")
        assert qa["grounded"]
        assert len(qa["sources"]) > 0
        assert "SENTINAL" in qa["answer"]

    def test_ingest_markdown(self, tmp_dir, sample_md, config):
        from sentinal.pipeline import Pipeline
        pipeline = Pipeline(config)
        result = pipeline.ingest(sample_md)
        assert result["chunk_count"] > 0

    def test_stats_after_ingest(self, tmp_dir, sample_txt, config):
        from sentinal.pipeline import Pipeline
        pipeline = Pipeline(config)
        pipeline.ingest(sample_txt)
        s = pipeline.stats()
        assert s["storage"]["documents"] >= 1
        assert s["storage"]["chunks"] >= 1
        assert s["index"]["chunks"] >= 1

    def test_ask_no_documents(self, config):
        from sentinal.pipeline import Pipeline
        pipeline = Pipeline(config)
        result = pipeline.ask("anything")
        assert not result["grounded"]
        assert "ingest" in result["answer"].lower()

    def test_persistence_survives_restart(self, tmp_dir, sample_txt, config):
        """Index and metadata should be usable after recreating Pipeline."""
        from sentinal.pipeline import Pipeline
        p1 = Pipeline(config)
        p1.ingest(sample_txt)

        p2 = Pipeline(config)  # New instance — loads from disk
        hits = p2.search("SENTINAL offline")
        assert len(hits) > 0


# ===========================================================================
# Doctor
# ===========================================================================

class TestDoctor:
    def test_doctor_runs(self, config):
        from sentinal.doctor import run_doctor
        report = run_doctor(config)
        assert report.checks
        assert report.summary()

    def test_doctor_detects_missing_data_dir(self, tmp_dir):
        from sentinal.config import SentinalConfig
        from sentinal.doctor import run_doctor
        cfg = SentinalConfig(data_dir=tmp_dir / "nonexistent_dir")
        report = run_doctor(cfg)
        data_check = next(c for c in report.checks if c.name == "Data directory")
        assert not data_check.passed

    def test_doctor_healthy_after_init(self, tmp_dir, config):
        from sentinal.doctor import run_doctor
        config.data_dir.mkdir(parents=True, exist_ok=True)
        config.index_path.mkdir(parents=True, exist_ok=True)
        report = run_doctor(config)
        # At minimum data_dir and index checks should pass
        data_check = next(c for c in report.checks if c.name == "Data directory")
        assert data_check.passed
