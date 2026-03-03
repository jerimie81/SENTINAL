# SENTINAL — Claude Coding Instruction Set

Use this document as the **execution brief** for implementing SENTINAL. You are expected to make production-quality, incremental changes with tests and documentation updates at each step.

---

## 1) Mission and Operating Constraints

### Mission
Build SENTINAL into a reliable, offline-first local AI knowledge system that supports:
- document ingestion,
- chunking and indexing,
- search and question answering,
- repeatable local operation on constrained hardware.

### Non-negotiable constraints
1. **Offline-first baseline**
   - Core workflows must run without internet access.
   - Optional cloud integrations must be isolated and never break local mode.
2. **Deterministic core path**
   - Same inputs + config should yield stable outputs where feasible.
3. **Security and privacy by default**
   - No hidden telemetry.
   - Sensitive values redacted from logs.
4. **Small, reviewable increments**
   - Prefer many focused commits over one large rewrite.

---

## 2) Repository Awareness and Working Rules

### Current project structure (high-level)
- `src/sentinal/` — core ingestion/chunking/index/qa modules.
- `src/flash_ai/` — service and engine layer.
- `tests/` — current automated tests.
- `README.md` — project documentation.

### Working rules
1. Preserve backward compatibility unless explicitly noted.
2. Avoid breaking public APIs without updating docs + tests.
3. Keep functions small and typed.
4. Add docstrings to public classes/functions.
5. Update README when behavior or CLI/API changes.
6. Add/extend tests in the same PR for every behavior change.

---

## 3) Definition of Done (global)

A task is only complete when **all** are true:
- [ ] Code compiles/runs locally.
- [ ] Unit tests for changed logic are added/updated.
- [ ] Integration path is validated for affected workflow.
- [ ] README and inline docs are updated.
- [ ] Error messages are actionable.
- [ ] Logging avoids leaking secrets.

---

## 4) Execution Plan (Implement in Order)

## Phase A — Stabilize Foundation

### A1. Configuration hardening
**Goals**
- Formalize config loading and validation.
- Support environment variable overrides.

**Implementation tasks**
- [ ] Introduce explicit config schema with types and defaults.
- [ ] Add validation with clear exceptions (invalid ranges, missing required keys).
- [ ] Add profile concept: `dev`, `prod`, `airgap`, `edge_lowmem`.
- [ ] Add persisted local config file support (e.g., `.sentinal/config.toml`).

**Acceptance criteria**
- Invalid config yields readable, deterministic errors.
- Profiles can be selected and override defaults predictably.

### A2. Logging and diagnostics
**Goals**
- Make runtime behavior observable without external services.

**Implementation tasks**
- [ ] Add structured logging mode (JSON) and human-readable mode.
- [ ] Add redaction for sensitive fields.
- [ ] Add a lightweight diagnostics command/path ("doctor" checks).

**Acceptance criteria**
- Logs include contextual fields (module, operation, duration).
- Redaction is covered by tests.

### A3. Error model
**Goals**
- Standardize exceptions and error surfaces.

**Implementation tasks**
- [ ] Define domain exception hierarchy (`ConfigError`, `IngestionError`, `IndexError`, etc.).
- [ ] Normalize user-facing error messages for CLI/service layers.
- [ ] Add retry/backoff helper for transient local I/O issues.

**Acceptance criteria**
- Known failure classes map to predictable error types.

---

## Phase B — Ingestion Pipeline Reliability

### B1. Source adapters
**Goals**
- Support robust file ingestion through clear adapter interfaces.

**Implementation tasks**
- [ ] Create adapter abstraction for document sources.
- [ ] Implement local file adapters for `txt`, `md`, `pdf`, `docx`.
- [ ] Add metadata normalization (`source_uri`, checksum, mime type, size, modified time).

**Acceptance criteria**
- Mixed-format ingestion works consistently with metadata attached.

### B2. Parsing + normalization
**Goals**
- Improve extracted text quality before chunking.

**Implementation tasks**
- [ ] Add normalization pipeline (unicode cleanup, whitespace normalization).
- [ ] Add optional boilerplate stripping heuristics.
- [ ] Preserve structure hints where possible (headings/lists).
- [ ] Add deduplication by checksum and near-duplicate detection.

**Acceptance criteria**
- Duplicate content is not re-indexed unless forced.

### B3. Chunking upgrades
**Goals**
- Improve chunk quality and traceability.

**Implementation tasks**
- [ ] Add token-aware chunking strategy.
- [ ] Support strategy modes: sentence / semantic-ish / fixed-token.
- [ ] Generate deterministic chunk IDs.
- [ ] Track provenance mapping from chunk -> original document offsets.

**Acceptance criteria**
- Chunking is deterministic and configurable.
- Retrieval can cite chunk provenance.

---

## Phase C — Indexing and Retrieval Quality

### C1. Embeddings architecture
**Goals**
- Keep default fallback while enabling better local embeddings.

**Implementation tasks**
- [ ] Preserve `HashEmbedder` as guaranteed fallback.
- [ ] Add pluggable embedder interface for local model backends.
- [ ] Cache embeddings by `(content_hash, model_id, model_version)`.

**Acceptance criteria**
- Changing model version invalidates cache safely.

### C2. Persistent index
**Goals**
- Durable index with maintenance operations.

**Implementation tasks**
- [ ] Introduce index persistence abstraction.
- [ ] Add rebuild and compaction paths.
- [ ] Add integrity check/corruption detection path.

**Acceptance criteria**
- Index survives process restarts.
- Corruption is detected with actionable remediation.

### C3. Retrieval improvements
**Goals**
- Improve relevance and diversity of retrieved contexts.

**Implementation tasks**
- [ ] Add hybrid retrieval option (lexical + vector fusion).
- [ ] Add metadata filtering.
- [ ] Add reranker abstraction (optional local reranker).
- [ ] Add MMR/diversity controls.

**Acceptance criteria**
- Retrieval quality measured with basic evaluation harness.

---

## Phase D — QA and Safety

### D1. Answer generation
**Goals**
- Upgrade answer synthesis from simple concatenation.

**Implementation tasks**
- [ ] Add template-driven synthesis logic.
- [ ] Enforce per-claim citation mapping where feasible.
- [ ] Add confidence/uncertainty signaling.
- [ ] Add output style controls (brief/detailed/bullet).

**Acceptance criteria**
- Answers clearly separate grounded facts from uncertainty.

### D2. Guardrails
**Goals**
- Reduce unsafe or ungrounded outputs.

**Implementation tasks**
- [ ] Add prompt-injection pattern checks on retrieved content.
- [ ] Add citation-required mode.
- [ ] Add basic hallucination heuristics (claim unsupported by sources).

**Acceptance criteria**
- Unsupported claims are flagged or rejected in strict mode.

---

## Phase E — Interfaces and UX

### E1. CLI first
**Goals**
- Establish CLI as primary user interface.

**Implementation tasks**
- [ ] Add command groups: `init`, `ingest`, `search`, `ask`, `stats`, `doctor`.
- [ ] Add `--json` output mode.
- [ ] Add examples in `--help` output.

**Acceptance criteria**
- End-to-end workflow works from CLI without editing code.

### E2. Local API (optional after CLI)
**Goals**
- Expose key functions via local HTTP API.

**Implementation tasks**
- [ ] Define OpenAPI contract for ingest/search/ask.
- [ ] Implement request validation and bounded payload sizes.
- [ ] Add local auth token option if multi-user scenario exists.

**Acceptance criteria**
- API and CLI behavior remain consistent.

---

## Phase F — Security, Ops, and Portability

### F1. Data protection
- [ ] Add encryption-at-rest for persisted state.
- [ ] Add key management mode (passphrase + keyring fallback).
- [ ] Add secure export/import with manifest + integrity verification.

### F2. Operational readiness
- [ ] Add migration framework for persisted schemas.
- [ ] Add backup/restore flow.
- [ ] Add performance profiling hooks (ingest throughput, query latency).

### F3. Supply chain hygiene
- [ ] Add SBOM generation.
- [ ] Add dependency/license checks.
- [ ] Add reproducible build guidance.

---

## 5) Testing Strategy (Required)

For each phase, add tests at multiple levels.

### Unit tests
- [ ] Pure logic (chunking boundaries, config validation, ranking math).
- [ ] Error behavior and edge cases.

### Integration tests
- [ ] Ingest -> index -> search -> ask happy path.
- [ ] Restart persistence tests.
- [ ] Corruption/failure-path tests where feasible.

### Regression tests
- [ ] Add fixtures for previous bugs.
- [ ] Add deterministic expected outputs for baseline flows.

### Quality gates (CI)
- [ ] Lint + format checks.
- [ ] Type checks.
- [ ] Test suite with coverage threshold.

---

## 6) Suggested PR Breakdown

Use this approximate sequence for manageable reviews:
1. PR-1: Config + error model + logging foundation.
2. PR-2: Ingestion adapter interfaces + metadata normalization.
3. PR-3: Chunking strategies + deterministic chunk IDs + tests.
4. PR-4: Persistent index + integrity checks.
5. PR-5: Retrieval improvements (hybrid + filtering + rerank abstraction).
6. PR-6: QA synthesis + citation enforcement + safety checks.
7. PR-7: CLI completion and doctor/stats commands.
8. PR-8: Security/backup/migration hardening.

Each PR must include:
- scope summary,
- test evidence,
- migration notes,
- rollback plan.

---

## 7) Implementation Prompt Template (Use with Claude per task)

When starting any task, use this prompt format:

```text
You are implementing SENTINAL in small, production-ready increments.

Task:
<describe one focused task from TODO>

Constraints:
- Preserve offline-first behavior.
- Keep deterministic baseline behavior.
- Add/adjust tests with code changes.
- Update README/docs for user-visible changes.
- Avoid breaking existing public interfaces unless explicitly approved.

Output requirements:
1) Brief design summary.
2) File-by-file change plan.
3) Code changes.
4) Tests added/updated.
5) Validation commands and expected results.
6) Risks + follow-up TODOs.
```

---

## 8) Immediate Next Sprint (Actionable)

Execute these in order first:
- [ ] Build CLI skeleton for `init`, `ingest`, `search`, `ask`.
- [ ] Add persistent metadata storage (SQLite) and simple index persistence.
- [ ] Implement adapter-based ingestion for `txt`/`md`/`pdf`.
- [ ] Add deterministic integration fixture for ingest->ask baseline.
- [ ] Implement `doctor` with basic environment and index checks.

Deliver sprint with:
- passing tests,
- updated README usage examples,
- migration notes for local state.

---

## 9) Completion Signal for Claude

When all checklist items for a task are done, report using:
- **Implemented**: concise summary
- **Tests**: commands + pass/fail
- **Docs Updated**: yes/no + files
- **Known Gaps**: explicit list
- **Next Task Recommendation**: single best next step
