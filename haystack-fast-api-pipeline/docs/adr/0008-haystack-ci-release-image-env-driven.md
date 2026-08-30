# ADR 0008: Haystack Release image takes estate config from the environment and product defaults from sanitized `.env.prod`

- **Status:** Accepted
- **Date:** 2026-08-18
- **Amended:** 2026-08-18 — sanitized `.env.prod` → `/app/.env` for product knobs; estate keys still not baked; Packaging does not read Environment `academy`. 2026-08-30 — compose workers are ADR 0011 images, not this Release image
- **Change:** `add-haystack-ci-pipeline` (image contract)
- **Related:** [0004](0004-haystack-env-aliases-and-uv-sidecars.md) (CD injects SM + overlay), [0007](0007-haystack-ci-stops-at-packaging.md), [0009](0009-haystack-project-profile-vs-infra-estate.md), [0011](0011-devcontainer-worker-sidecars.md) (compose workers are not this image)

## Context

Academy compose uses the Release image for **uvicorn only**. `postgres-haystack-sync` and `neo4j-populate` are estate/CD scripts on `postgres:17` and `python:3.12-slim` ([ADR 0011](0011-devcontainer-worker-sidecars.md)); they are not this image. Infra `sync-secrets` (estate ground truth) writes `heavy-rental/haystack`: Haystack RDS `POSTGRES_*` / `DATABASE_URL`, `SOURCE_*` (SoR), `TARGET_*` (Haystack RDS), `FLEET_BACKEND=sql`, `NEO4J_BACKEND=bolt`, `NEO4J_URI` (Bolt NLB), `NEO4J_POPULATE_URL` (compose worker on `asg-haystack`), user / password, and optional `LLM_API_KEY`. Product knobs (`NEED_DECOMPOSER`, other `LLM_*`, `INDEXING_*`, `KG_*`, …) are Haystack Environment `academy` or `AWS_ACTUAL` (ADR 0009) and/or a sanitized `.env.prod` shipped as `/app/.env`, not Dockerfile `ENV`. Baking estate hosts or secrets into the image would pin every tag to one lab or leak a key.

## Decision

Release Packaging **always generates** `python:3.12-slim-bookworm` + uv + `uvicorn app.main:app --host 0.0.0.0 --port 8000` (an app `Dockerfile` is not the deploy image) with **no** `ENV`/`ARG` for infra SM keys or Profile knobs. It sanitizes the app checkout `.env.prod` (or `docs/samples/.env.prod`, or generated production defaults), **drops estate keys** (`POSTGRES_*`, `DATABASE_URL`, `SOURCE_*`, `TARGET_*`, `NEO4J_URI` / `USER` / `PASSWORD`, `NEO4J_POPULATE_URL`, `LLM_API_KEY`), and `COPY`s the result as `/app/.env` so pydantic `Settings` (`env_file=".env"`) loads product defaults (`APP_ENV=prod`, indexing, fleet flags, …). A raw `COPY .env` is still refused. Process env (Academy compose `env_file` from SM + overlay, or `docker run -e`) **wins** over the file. After `docker build`, Packaging inspects `Config.Env` (no baked estate/knob `ENV`), proves `/app/.env` loaded `Settings().app_env` and that `-e APP_ENV=…` overrides it, proves dummy infra keys **and** the listed knobs are visible via `-e`, and starts uvicorn only long enough to prove `GET /docs` or `GET /health` on `:8000` returns 200–302. It does not connect to RDS or an LLM. Sidecar packages are copied only if the checkout already has them.

## Consequences

- The same image tag works on Docker Desktop (`docker run -p 8000:8000 -e …`), compose (uvicorn service), or any Academy lab. Product knobs have production-shaped file defaults; estate URLs still come from infra `sync-secrets`.
- An app `Dockerfile` is moved aside; it is not pushed to GHCR.
- Packaging may `COPY` sidecar Python packages if those directories exist; CD workers do not use them (ADR 0011). Missing `postgres_haystack_sync` is a warning, not a red Release.
- Sample checklist: [`../samples/.env.prod`](../samples/.env.prod). Copy it to the app repo as `.env.prod` so Packaging uses the operator file instead of generated defaults.
- Packaging does **not** read Haystack Environment `academy` or `AWS_ACTUAL`. Setting a GitHub Profile variable does not change the image (ADR 0009).
