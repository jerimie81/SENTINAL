# Flash-AI (Initial Scaffold)

This repository now contains an initial, runnable Python scaffold for Flash-AI:

- `flash_ai.engine`: deterministic flashcard generation logic
- `flash_ai.service`: application service layer with in-memory deck storage
- `flash_ai.models`: core domain models
- `tests/`: starter tests for generation and service behavior

## Why this scaffold

The file `Flash-AI_Technical-Design-Manual-(TDM).PDF` currently has zero bytes in this repository,
so this scaffold establishes a clean foundation that can be aligned to the full TDM once the
manual content is available.

## Run tests

```bash
python -m pytest -q
```
