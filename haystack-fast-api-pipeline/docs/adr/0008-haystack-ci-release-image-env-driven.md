# ADR 0008: Haystack Release image takes DB and sync config from the environment

- **Status:** Accepted
- **Date:** 2026-08-18
- **Change:** `add-haystack-ci-pipeline` (image contract)
- **Related:** [0004](0004-haystack-env-aliases-and-uv-sidecars.md) (CD injects SM + overlay), [0007](0007-haystack-ci-stops-at-packaging.md), [0009](0009-haystack-project-profile-vs-infra-estate.md)

## Context

Academy compose reuses the Release image for uvicorn, `postgres-haystack-sync`, and `neo4j-populate`. Infra `sync-secrets` (estate ground truth) writes `heavy-rental/haystack`: Haystack RDS `POSTGRES_*` / `DATABASE_URL`, `SOURCE_*` (SoR), `TARGET_*` (Haystack RDS), `FLEET_BACKEND=sql`, `NEO4J_BACKEND=bolt`, `NEO4J_URI` (Bolt NLB), `NEO4J_POPULATE_URL` (compose worker on `asg-haystack`), user / password, and optional `LLM_API_KEY`. Product knobs (`NEED_DECOMPOSER`, other `LLM_*`, `INDEXING_*`, `KG_*`, …) are Haystack Environment `academy` (ADR 0009), not Dockerfile `ENV`. Baking any of those into the image would pin every tag to one estate or leak a key.

## Decision

Release Packaging **always generates** `python:3.12-slim-bookworm` + uv + `uvicorn app.main:app --host 0.0.0.0 --port 8000` (an app `Dockerfile` is not the deploy image) with **no** `ENV`/`ARG` for infra SM keys or `.env.example` knobs, and no `.env` copy. After `docker build`, it inspects `Config.Env`, proves dummy infra keys **and** the listed knobs are visible via `-e`, and starts uvicorn only long enough to prove `GET /docs` or `GET /health` on `:8000` returns 200–302. It does not connect to RDS or an LLM. Sidecar packages are copied only if the checkout already has them.

## Consequences

- The same image tag works on Docker Desktop (`docker run -p 8000:8000 -e …`), compose, or any Academy lab once infra `sync-secrets` + guest `.env` are injected.
- An app `Dockerfile` is moved aside; it is not pushed to GHCR.
- Missing `postgres_haystack_sync` is a warning, not a red Release (app `develop` still lacks the module).
