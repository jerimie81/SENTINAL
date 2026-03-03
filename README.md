# SENTINAL + Flash-AI

This repository contains two local-first Python components:

- `sentinal`: offline ingestion/index/search/QA pipeline with a Click CLI.
- `flash_ai`: deterministic flashcard generation scaffold.

## SENTINAL quickstart

Run CLI commands with `PYTHONPATH=src`:

```bash
PYTHONPATH=src python -m sentinal.cli_py init
PYTHONPATH=src python -m sentinal.cli_py ingest ./docs/notes.md
PYTHONPATH=src python -m sentinal.cli_py search "offline first"
PYTHONPATH=src python -m sentinal.cli_py ask "What does SENTINAL do?"
```

You can switch to JSON output with `--json` and choose config profiles (`dev`, `prod`, `airgap`, `edge_lowmem`) via `--profile`.

## Run tests

```bash
PYTHONPATH=src python -m pytest -q
```
