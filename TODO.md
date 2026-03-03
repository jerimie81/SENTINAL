# SENTINAL TODO

Comprehensive implementation plan for **SENTINAL – Portable Offline AI System**.

---

## 0) Guiding Principles

- **Offline-first:** all core capabilities must function without internet.
- **Portable:** runnable on constrained hardware (laptop, edge device, field workstation).
- **Deterministic core path:** baseline behavior reproducible across runs.
- **Security by default:** local encryption, least privilege, auditable actions.
- **Progressive enhancement:** optional model/provider integrations must not break offline baseline.

---

## 1) Foundation & Architecture (Highest Priority)

### 1.1 Runtime + packaging
- [ ] Add lockfile + reproducible dependency management strategy.
- [ ] Define supported Python matrix and CI test matrix.
- [ ] Add package entrypoints (`sentinal-cli`) and version command.
- [ ] Create semantic versioning and release checklist.

### 1.2 Configuration system
- [ ] Extend config to support environment-variable overrides.
- [ ] Add config validation layer (types + range checks + clear errors).
- [ ] Add profile support (`dev`, `prod`, `airgap`, `edge-lowmem`).
- [ ] Add persisted app config in `.sentinal/config.toml`.

### 1.3 Logging, telemetry, diagnostics
- [ ] Add structured logging (JSON + human modes).
- [ ] Introduce log redaction for sensitive fields.
- [ ] Add local diagnostics command (`sentinal doctor`).
- [ ] Add optional offline metrics sink (local file/SQLite).

### 1.4 Error handling model
- [ ] Define domain exception hierarchy.
- [ ] Normalize error codes/messages for CLI/API surfaces.
- [ ] Add retry/backoff primitives for local I/O contention.

---

## 2) Knowledge Ingestion Pipeline

### 2.1 Source adapters
- [ ] Add filesystem ingestion (txt/md/pdf/docx) with adapter interfaces.
- [ ] Implement robust PDF extraction fallback chain.
- [ ] Add incremental directory watcher mode (polling + debounce).
- [ ] Add source metadata normalization (`source_uri`, checksum, mime, size).

### 2.2 Parsing + cleaning
- [ ] Add language detection and text normalization.
- [ ] Remove boilerplate/headers/footers with heuristics.
- [ ] Preserve structural hints (headings, bullet lists, tables-as-text).
- [ ] Add deduplication by document checksum and near-duplicate chunk similarity.

### 2.3 Chunking improvements
- [ ] Add token-aware chunking strategy (vs words only).
- [ ] Add strategy selection (`sentence`, `semantic`, `fixed-token`).
- [ ] Add deterministic chunk IDs and provenance mapping.
- [ ] Add benchmark suite for chunk quality and speed.

---

## 3) Embeddings & Retrieval

### 3.1 Embedding providers
- [ ] Keep `HashEmbedder` as fallback baseline.
- [ ] Add local model embedding provider interface (GGUF/ONNX backends).
- [ ] Add pluggable model registry and selection policy.
- [ ] Cache embeddings by content hash and model/version.

### 3.2 Indexing
- [ ] Add persistent vector store abstraction (SQLite + ANN backend option).
- [ ] Support index rebuild, compaction, and corruption detection.
- [ ] Add hybrid retrieval (BM25 + vector fusion).
- [ ] Add metadata filters (date, tag, source, classification).

### 3.3 Retrieval quality
- [ ] Add reranker abstraction (local cross-encoder optional).
- [ ] Add MMR diversity and anti-duplication controls.
- [ ] Add query expansion + rewrite hooks.
- [ ] Build retrieval evaluation harness (precision@k, recall@k, MRR).

---

## 4) QA / Reasoning Layer

### 4.1 Answer synthesis
- [ ] Replace snippet concatenation with template-driven synthesis.
- [ ] Enforce explicit citation mapping per claim.
- [ ] Add confidence scoring and uncertainty messaging.
- [ ] Add answer length and style controls.

### 4.2 Guardrails
- [ ] Add prompt-injection detection for retrieved content.
- [ ] Add policy filters for unsafe output categories.
- [ ] Add citation-required mode (deny unsupported claims).
- [ ] Add hallucination heuristics (claim-vs-source checks).

### 4.3 Conversation/session support
- [ ] Add local session memory with TTL.
- [ ] Add topic-scoped context windows.
- [ ] Add conversation export/import for field use.

---

## 5) Security & Privacy

### 5.1 Data protection
- [ ] Encrypt at rest for `.sentinal` state.
- [ ] Add key management mode (passphrase + OS keyring fallback).
- [ ] Implement secure delete option for sensitive datasets.
- [ ] Add signed backup/restore flow.

### 5.2 Access control
- [ ] Add local RBAC roles for multi-user hosts.
- [ ] Add audit log for ingestion/query/admin actions.
- [ ] Add API auth tokens with rotation policies.

### 5.3 Supply chain
- [ ] Add SBOM generation in releases.
- [ ] Add dependency/license policy checks.
- [ ] Add reproducible build verification artifacts.

---

## 6) Interfaces (CLI + API + Optional UI)

### 6.1 CLI (priority)
- [ ] Add commands: `init`, `ingest`, `search`, `ask`, `stats`, `doctor`.
- [ ] Add machine-readable output mode (`--json`).
- [ ] Add shell completion and command help examples.

### 6.2 Local API
- [ ] Define REST/HTTP API contract for ingestion/search/ask.
- [ ] Add OpenAPI schema generation.
- [ ] Add rate limiting and request size controls.

### 6.3 Optional UI
- [ ] Build minimal local web UI for ingest/search/ask.
- [ ] Add source citation drill-down panel.
- [ ] Add offline status + model/index health indicators.

---

## 7) Persistence & Operations

### 7.1 State management
- [ ] Add repository metadata DB (SQLite) for docs/chunks/index versions.
- [ ] Add schema migration framework.
- [ ] Add transactional ingestion with rollback on failure.

### 7.2 Backup & portability
- [ ] Implement portable export bundle (state + docs + manifest).
- [ ] Implement integrity verification for imports.
- [ ] Add differential backup mode for large corpora.

### 7.3 Performance
- [ ] Add ingestion throughput benchmarks.
- [ ] Add query latency budgets and profiling hooks.
- [ ] Add memory ceilings and adaptive batching.

---

## 8) Testing & Quality

### 8.1 Test strategy
- [ ] Expand unit tests across all modules and edge cases.
- [ ] Add integration tests for end-to-end ingest/search/ask.
- [ ] Add golden tests for deterministic offline baseline.
- [ ] Add property tests for chunking/index correctness.

### 8.2 Reliability
- [ ] Add fuzzing for parsers and ingestion adapters.
- [ ] Add fault-injection tests (disk full, corrupt index, interrupted writes).
- [ ] Add chaos-style long-run tests for memory leaks/regressions.

### 8.3 Code quality gates
- [ ] Add linting/format/type gates in CI.
- [ ] Add coverage threshold + diff coverage checks.
- [ ] Add conventional commit / PR template checks.

---

## 9) Documentation & Developer Experience

### 9.1 Docs
- [ ] Add architecture decision records (ADRs).
- [ ] Add threat model and security hardening guide.
- [ ] Add offline deployment playbook and troubleshooting guide.

### 9.2 Onboarding
- [ ] Add `examples/` for common workflows.
- [ ] Add `make`/task runner targets for common dev actions.
- [ ] Add contributor guide with coding/testing standards.

---

## 10) Milestones

### Milestone A — Core Offline MVP
- [ ] CLI for ingest/search/ask.
- [ ] Persistent local index + metadata DB.
- [ ] Deterministic baseline tests + integration tests.
- [ ] Basic security controls (encryption at rest + audit log).

### Milestone B — Quality & Safety
- [ ] Retrieval evaluation harness and reranking.
- [ ] Guardrails and citation-required QA mode.
- [ ] Backup/export + migration stability.

### Milestone C — Field-Ready Operations
- [ ] Performance tuning for constrained devices.
- [ ] Air-gapped installation + update process.
- [ ] Full operational playbook and diagnostics tooling.

---

## 11) Immediate Next Sprint (Recommended)

- [ ] Implement CLI skeleton (`init`, `ingest`, `search`, `ask`).
- [ ] Add persistent storage layer (SQLite metadata + vector persistence).
- [ ] Introduce adapter-based ingestion for txt/md/pdf.
- [ ] Add deterministic end-to-end integration test fixture.
- [ ] Add structured logging + `sentinal doctor` basic checks.
