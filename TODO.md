# TODO.md — SENTINAL Build Plan + Claude Execution Brief

This file is designed as **direct user input for Claude** when asking it to implement SENTINAL.
Use it as both:
1) a product roadmap, and
2) an execution contract for how coding tasks should be delivered.

---

## 0) Copy/Paste Starter Prompt for Claude

```text
You are implementing SENTINAL from the repository TODO.md.

Follow TODO.md exactly as the source of truth.
Work in small, production-safe increments.
For each task:
1) propose a short implementation plan,
2) make minimal file changes,
3) add/adjust tests,
4) run validations,
5) summarize with risks + next step.

Hard constraints:
- Keep offline-first behavior functional.
- Preserve deterministic behavior where possible.
- Do not break existing tests.
- Update README/docs for any user-visible change.
- Prefer backward-compatible changes.
```

---

## 1) Project Mission and Quality Bar

### Mission
Deliver a portable, offline-first local AI system that can:
- ingest local knowledge files,
- chunk and index content,
- retrieve relevant passages,
- answer questions with traceable sources.

### Quality bar (non-negotiable)
- **Offline baseline works without internet.**
- **Deterministic baseline path is testable.**
- **Security/privacy defaults are safe.**
- **Every behavior change includes tests.**
- **Changes are incremental and reviewable.**

---

## 2) Current Repo Map (for Claude orientation)

Primary modules:
- `src/sentinal/config.py` — runtime configuration
- `src/sentinal/chunking.py` — chunking strategies
- `src/sentinal/embeddings.py` — embedding logic/fallbacks
- `src/sentinal/index.py` — indexing/retrieval primitives
- `src/sentinal/qa.py` — QA orchestration
- `src/sentinal/knowledge_base.py` — ingestion/search composition
- `src/flash_ai/engine.py`, `src/flash_ai/service.py` — service/engine layer

Tests currently live in:
- `tests/test_sentinal_core.py`
- `tests/test_engine.py`

---

## 3) Global Definition of Done (DoD)

A task is complete only if all items pass:
- [ ] Code builds/runs locally.
- [ ] New/changed logic has unit tests.
- [ ] Impacted flow has integration coverage (or documented gap).
- [ ] Existing tests still pass.
- [ ] README/docs updated for user-facing changes.
- [ ] Error messages are actionable.
- [ ] Logging does not leak sensitive values.

---

## 4) Implementation Rules for Claude

1. **Work in one focused PR-sized unit at a time.**
2. **Do not perform broad refactors without explicit request.**
3. **Preserve public APIs unless migration notes are added.**
4. **Use typed function signatures and concise docstrings.**
5. **Add feature flags/toggles for risky behavior changes.**
6. **Prefer pure functions for deterministic logic.**
7. **If a dependency is added, justify why stdlib/current deps are insufficient.**

---

## 5) Priority Roadmap (Execution Order)

## Phase A — Foundation Hardening

### A1. Config system
- [ ] Add schema-style validation (types + ranges + required fields).
- [ ] Add env-var override support.
- [ ] Add profile support: `dev`, `prod`, `airgap`, `edge_lowmem`.
- [ ] Add persisted config path: `.sentinal/config.toml`.

**Acceptance checks**
- Invalid config returns deterministic, human-readable errors.
- Profile resolution order is documented and tested.

### A2. Logging + diagnostics
- [ ] Add human + JSON logging modes.
- [ ] Redact secrets/tokens/credentials in logs.
- [ ] Add `doctor` diagnostics path/command.

**Acceptance checks**
- Log lines include operation context and duration where relevant.
- Redaction behavior is unit tested.

### A3. Error model
- [ ] Introduce domain exceptions (`ConfigError`, `IngestionError`, `IndexError`, `QAError`).
- [ ] Normalize service/CLI-facing error responses.
- [ ] Add retry/backoff utility for transient file I/O conflicts.

**Acceptance checks**
- Common failures map to stable exception categories.

---

## Phase B — Ingestion Reliability

### B1. Adapter architecture
- [ ] Create source adapter interface.
- [ ] Implement adapters for `txt`, `md`, `pdf`, `docx`.
- [ ] Normalize metadata: `source_uri`, checksum, mime, size, modified time.

### B2. Parse/clean pipeline
- [ ] Unicode + whitespace normalization.
- [ ] Optional boilerplate/header/footer removal.
- [ ] Preserve useful structure hints (titles/lists/table text).
- [ ] Deduplicate by checksum and near-duplicate similarity threshold.

### B3. Chunking improvements
- [ ] Add token-aware chunking mode.
- [ ] Support `sentence`, `fixed-token`, and semantic-leaning strategies.
- [ ] Deterministic chunk IDs.
- [ ] Provenance offsets for citation mapping.

---

## Phase C — Embeddings, Indexing, Retrieval

### C1. Embeddings
- [ ] Keep `HashEmbedder` as guaranteed fallback.
- [ ] Add pluggable local embedder interface.
- [ ] Cache embeddings by `(content_hash, model_id, model_version)`.

### C2. Persistent index
- [ ] Add persistence abstraction (initial SQLite-backed implementation acceptable).
- [ ] Add index rebuild + compaction flow.
- [ ] Add integrity/corruption checks.

### C3. Retrieval quality
- [ ] Hybrid retrieval option (lexical + vector).
- [ ] Metadata filters.
- [ ] Optional reranker abstraction.
- [ ] MMR/diversity controls.
- [ ] Evaluation harness: precision@k, recall@k, MRR.

---

## Phase D — QA Grounding and Safety

### D1. Answer synthesis
- [ ] Replace naive concatenation with template-driven synthesis.
- [ ] Require citation mapping for grounded claims where possible.
- [ ] Add confidence/uncertainty messaging.
- [ ] Add output style controls (brief/detailed/bullets).

### D2. Safety guardrails
- [ ] Detect likely prompt injection patterns in retrieved content.
- [ ] Add strict citation-required mode.
- [ ] Add unsupported-claim detection heuristics.

---

## Phase E — Interfaces

### E1. CLI (first-class)
- [ ] Add/complete commands: `init`, `ingest`, `search`, `ask`, `stats`, `doctor`.
- [ ] Add `--json` machine-readable output.
- [ ] Add practical help examples.

### E2. Local API (after CLI stability)
- [ ] Define OpenAPI contract for ingest/search/ask.
- [ ] Validate payload sizes and request schemas.
- [ ] Add optional local token auth for multi-user hosts.

---

## Phase F — Security + Operations

- [ ] Encryption at rest for persisted state.
- [ ] Key management mode (passphrase + keyring fallback).
- [ ] Export/import bundles with integrity manifest.
- [ ] Migration framework for persistent schemas.
- [ ] Backup/restore workflows.
- [ ] Performance hooks (ingestion throughput + query latency).
- [ ] SBOM + dependency/license checks for releases.

---

## 6) Mandatory Testing Policy

For every completed task, Claude must run relevant checks and report output.

Minimum expected commands:
- `pytest -q`
- Any targeted test selection for changed modules (example: `pytest -q tests/test_sentinal_core.py`)

If a command cannot run, Claude must explicitly explain why and propose a workaround.

---

## 7) Recommended PR Slicing

1. Config validation + profiles + env overrides
2. Error hierarchy + logging + doctor
3. Ingestion adapters + metadata normalization
4. Chunking deterministic IDs + provenance
5. Persistent index + integrity checks
6. Hybrid retrieval + filtering + evaluation harness
7. QA synthesis + citations + guardrails
8. CLI completion + docs examples
9. Security + backup/migrations + release hygiene

Each PR summary must include:
- Scope,
- Behavior changes,
- Tests executed,
- Risks,
- Follow-up TODO.

---

## 8) Task Execution Template (Claude must follow)

```text
Task: <single task from TODO>

Plan:
- <step 1>
- <step 2>

Changes:
- <file>: <what changed>

Tests:
- <command>
- <result>

Validation:
- <what behavior is now guaranteed>

Risks/Notes:
- <edge cases or deferred items>

Next recommended task:
- <single next item>
```

---

## 9) Immediate Next Sprint (first 5 tasks)

- [ ] Implement CLI skeleton: `init`, `ingest`, `search`, `ask`.
- [ ] Add SQLite metadata persistence for docs/chunks/index versions.
- [ ] Implement adapter-based ingestion for `txt`/`md`/`pdf` first.
- [ ] Add deterministic ingest→retrieve→ask integration fixture.
- [ ] Implement `doctor` with environment/index sanity checks.

Sprint exit criteria:
- [ ] `pytest -q` passes.
- [ ] README includes runnable usage examples.
- [ ] Migration/storage notes are documented.

---

## 10) Anti-Patterns to Avoid

- Giant one-shot rewrites.
- Adding network-dependent core behavior.
- Silent failures or swallowed exceptions.
- Unbounded memory growth in ingestion/indexing paths.
- Shipping new behavior without tests.
- Introducing breaking API changes without migration guidance.
