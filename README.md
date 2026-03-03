# SENTINAL – Portable Offline AI System

This repository now contains the **initial production-ready core** for SENTINAL's highest-priority offline components:

- Offline knowledge ingestion (document + chunking)
- Deterministic local embeddings for bootstrap environments
- Local vector index with similarity search
- Retrieval-QA service over local knowledge
- Path/config primitives for portable deployments

## Implemented modules

- `sentinal.config` – deployment paths + retrieval settings
- `sentinal.models` – `Document`, `Chunk`, `SearchResult`
- `sentinal.chunking` – chunking with overlap and validation
- `sentinal.embeddings` – deterministic offline `HashEmbedder`
- `sentinal.index` – in-memory vector index + top-k search
- `sentinal.knowledge_base` – document ingestion and retrieval API
- `sentinal.qa` – retrieval-backed answer service

## Run tests

```bash
python -m pytest -q
```
