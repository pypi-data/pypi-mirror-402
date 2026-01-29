# Repository Guidelines

## Project Structure & Modules
- `src/pagesmith/`: library source (splitters, parser, refiners). Entry metadata in `__about__.py`.
- `tests/`: pytest suite and fixtures; resources under `tests/resources/`.
- `docs/`: MkDocs config and localized content in `docs/src/<lang>/`.
- `scripts/`: utility scripts (versioning, docs, build).
- `tasks.py`: Invoke tasks (version bump, docs preview, pre-commit).

## Build, Test, and Development
- Environment: `. ./activate.sh` (requires Python 3.12 and Astral’s `uv`).
- Install deps: done automatically by `activate.sh` via `uv sync`.
- Lint/format/type-check: `invoke pre` (runs ruff, ruff-format, mypy via pre-commit).
- Run tests: `pytest` or `pytest -q` (doctests enabled via `pytest.ini`).
- Coverage: `pytest --cov` (config in `.coveragerc`).
- Docs preview: `invoke docs-en` (or `docs-ru`); serves MkDocs locally.
- Version bump: `invoke ver-bug|ver-feature|ver-release` (wrapper over `scripts/verup.sh`).

## Coding Style & Naming
- Python ≥3.10; target dev is 3.12.
- Indentation: 4 spaces; max line length ~99–100 (ruff/flake8 configured).
- Tools: ruff (lint/format), mypy (strict, src only), flake8 baseline.
- Naming: modules/functions/vars `snake_case`; classes `PascalCase`; constants `UPPER_CASE` (ruff N rules enforced).
- Imports: sorted/organized by ruff; prefer explicit exports in `__init__.py`.

## Testing Guidelines
- Framework: pytest (+ doctests).
- Layout: test files `tests/test_*.py`; test functions `test_*`.
- Coverage: include meaningful edge cases; heavy I/O or HTML fixtures in `tests/resources/`.
- Allure: results are written to `allure-results/` when configured.

## Commit & Pull Requests
- Commits: concise, present tense (e.g., `refactor parser`, `docs`); release commits use `Version vX.Y.Z …`.
- Branches: prefer `feature/<topic>` or `bug/<topic>` to match version types.
- Before PR: run `invoke pre` and `pytest`; ensure docs build (`invoke docs-en`) if docs changed.
- PR description: what/why, linked issues, screenshots for docs/UI, and notes on tests/coverage.

## Security & Configuration
- Do not commit secrets; docs/site configs live under `docs/` and are language-aware.
- Local config: prefer `activate.sh` + `uv`; avoid global environment mutations.
