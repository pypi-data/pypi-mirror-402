AGENTS for cat-experiments (root scope).
Use Python 3.12; always enable `from __future__ import annotations`.
Install dev deps via `uv sync --dev` (uv.lock present).
Run full test suite: `uv run pytest`.
Run single test: `uv run pytest tests/test_file.py::test_case`.
Tests live under `tests/` with `-v --tb=short` configured.
Lint imports/style with `uv run ruff check .` (E/F/W/I; sorted imports).
Autoformat with `uv run black .` (line length 100).
Type-check strictly with `uv run mypy src tests` (strict) or `uv run pyright`.
Prefer dataclasses and typed dictionaries for structured data.
Use standard containers (`list[str]`, `dict[str, Any]`) and explicit return types.
Keep functions and variables descriptive snake_case; avoid one-letter names.
Keep modules cohesive; favor small helpers over inline logic duplication.
Handle invalid inputs with explicit exceptions (e.g., `ValueError`) not silent fallback.
Preserve immutability of inputs when possible; copy before mutating collections.
Use context managers/async with for resources; propagate/attach errors instead of swallowing.
Imports: stdlib, third-party, local; no relative parent-hopping unless necessary.
Avoid inline comments; prefer clear naming and docstrings for public APIs.
Observers/evaluators should remain deterministic and side-effect minimal unless explicitly required.
No Cursor or Copilot repo rules present.
