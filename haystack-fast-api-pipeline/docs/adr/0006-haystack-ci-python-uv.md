# ADR 0006: Haystack CI toolchain is CPython 3.12 + uv

- **Status:** Accepted
- **Date:** 2026-08-17
- **Change:** `add-haystack-ci-pipeline`

## Context

Copy-pasting REST (Java 21 / Maven), portal (Node 22), or mobile (JDK 17 / Gradle) YAML would install the wrong toolchain. The app is already a uv project (`pyproject.toml`, `uv.lock`, `.python-version` 3.12).

## Decision

Integration uses `actions/setup-python` 3.12 and `astral-sh/setup-uv` with cache on `uv.lock`. Resolve is `uv lock --check` then `uv sync --frozen --all-groups`, then Haystack / FastAPI import smoke. QC is `uv run ruff check` + `uv run pytest`. Do not use pip/poetry/pdm as the installer. Do not `--extra neo4j` in CI.

## Consequences

- Semgrep `p/python`, pip-audit report, CodeQL `python`.
- Release `uv build` plus a generated `python:3.12-slim-bookworm` + uv + uvicorn image when the app has no Dockerfile.
- No `REST_API_DB_*`, no Android SDK, no `npm ci` on this family.
