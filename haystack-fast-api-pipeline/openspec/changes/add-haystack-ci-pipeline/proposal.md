# Proposal: Add haystack-fast-api GitHub Actions CI family

## Why

[Heavy-Rental/haystack-fast-api](https://github.com/Heavy-Rental/haystack-fast-api) has no GitHub Actions workflows. The REST API, web portal, and mobile app already share a reusable-caller GitHub Flow family (fast feedback, integration CI, release). The FastAPI + Haystack service needs the same gates so feature branches, PRs into `develop`, and a manual Release on `master` (`workflow_dispatch`) are validated consistently.

Copy-pasting those YAML files unchanged would install the **wrong toolchain** (Java 21 + Maven + Postgres, Android/Gradle, or Node 22 + Vite). This change uses **Python 3.12, uv, Ruff, pytest, and Haystack pipeline smoke** — the tools the application already declares in `pyproject.toml` / `QUICKSTART.md`.

## What Changes

- Add three reusable workflows plus three sole-allowed callers, authored in this pipeline-development repo under `haystack-fast-api-pipeline/`.
- Integration CI is the merge gate: Integration first, then Quality Control, Security Testing, and CodeQL in parallel, then an aggregate GitHub Flow CI Gate. On `pull_request`, Integration reuses a successful Fast Feedback run for the head SHA (the CI caller does not `uses:` Fast Feedback).
- Fast feedback runs Integration only on feature-branch pushes (sole Integration-stage run for that SHA).
- Release (`workflow_dispatch`) runs Integration + Quality Control, then Packaging (`uv build` + image tar), DAST, and Publish (public GHCR + GitHub Release). SAST and CodeQL stay on Integration CI. Packaging sanitizes `.env.prod` into `/app/.env` (product knobs only). Academy Environment variables are **not** read at Packaging (ADR 0009).
- Specify the pipelines with OpenSpec (behavior) and OpenSPDD (REASONS Canvas implementation contract).
- Bound the family to CI and packaging. Infrastructure, deploy, and operate are another project.

## Capabilities

### New Capabilities

- `haystack-ci-orchestration`: callers, triggers, concurrency, caller gate, checkout modes, Fast Feedback reuse
- `haystack-ci-integration`: Python 3.12, uv lock/sync, Haystack + FastAPI import smoke, layout checks; skip uv/layout when Fast Feedback already passed
- `haystack-ci-quality`: Ruff, pytest (Haystack pipeline + FastAPI TestClient, CI-safe backends)
- `haystack-ci-security`: Semgrep app + GHA (two passes) + pip-audit report + Trivy + SARIF
- `haystack-ci-codeql`: CodeQL python
- `haystack-ci-release`: `uv build` versioned wheel/sdist plus Docker image tar, DAST, then Publish (public GHCR + GitHub Release)
- `haystack-ci-scope`: this family stops at packaging; it does not provision infrastructure, deploy, or operate

### Modified Capabilities

- None (greenfield for this repo’s haystack pipelines).

## Impact

- **Application repo:** operators copy the six YAML files into `Heavy-Rental/haystack-fast-api` `.github/workflows/`.
- **This repo:** new `haystack-fast-api-pipeline/` tree (specs + workflows). No change to REST API, portal, or mobile pipelines.
- **Not in this change:** live pgvector/Neo4j/LLM CI, scheduled model retrain, committing an application Dockerfile as the deploy image (Release always generates uvicorn), edits to the application product OpenSpec, or infrastructure / operate workflows (another project). Academy app CD is a separate change in this tree.
