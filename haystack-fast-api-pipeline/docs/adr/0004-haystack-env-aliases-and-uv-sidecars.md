# ADR 0004: App env aliases and uv sidecar commands

- **Status:** Amended by [0011](0011-devcontainer-worker-sidecars.md)
- **Superseded sidecar commands:** `uv run python -m postgres_haystack_sync` / `neo4j_populate` — workers are now estate/CD scripts on `postgres:17` and `python:3.12-slim` (ADR 0011 / infra 0020). Env aliases and Profile overlay in this ADR still apply.
- **Date:** 2026-08-17
- **Change:** `add-haystack-cd-academy-deploy`
- **Amends:** [0003](0003-reuse-infra-haystack-ansible.md) (same three services; env post-process + sidecar entrypoint)
- **Related:** [0009](0009-haystack-project-profile-vs-infra-estate.md)

## Context

[Heavy-Rental/haystack-fast-api](https://github.com/Heavy-Rental/haystack-fast-api) `develop` reads `POSTGRES_HOSTNAME` / `POSTGRES_DB` / `POSTGRES_USER` and defaults `FLEET_BACKEND=fake`, `NEO4J_BACKEND=fake`. Infra `heavy-rental/haystack` writes `POSTGRES_HOST` / `DATABASE` / `USERNAME` and `NEO4J_URI` but not those live flags. The Release image uses `uv run`; estate compose used `python -m` (system Python, no venv).

## Decision

After `guest_base` maps SM → `.env`, the haystack role fills **missing** aliases and Academy live flags only, then overlays **Haystack Environment (`academy` or `AWS_ACTUAL`)** Profile knobs (`APP_ENV`, `NEED_DECOMPOSER`, `LLM_*`, `INDEXING_*`, `PRICING_SCHEMA`, `KG_*`, `PROJECT_AGENT_*`, …) when those GitHub variables/secrets are non-empty. Empty vars leave SM / image `/app/.env` (from `.env.prod`) / app defaults. The overlay SHALL NOT write `NEO4J_URI`, `NEO4J_POPULATE_URL`, `NEO4J_PASSWORD`, `POSTGRES_*`, `SOURCE_*`, or `TARGET_*`. Sidecar **commands** are superseded by [0011](0011-devcontainer-worker-sidecars.md). Services, limits, and the no-`neo4j` check stay as estate. Ansible fails if uvicorn never answers; worker failures do not fail `verify`.

`SOURCE_HOST` / `SOURCE_PORT` / `SOURCE_DATABASE` (SoR RDS) and `TARGET_HOST` / `TARGET_PORT` / `TARGET_DATABASE` (Haystack RDS) stay infra `sync-secrets` output. This CD does not invent those **hosts**, or read `heavy-rental/rest`. Worker **credential** aliases (`SOURCE_USER`, `TARGET_USER`, `PG*`, `NEO4J_POPULATE_TRIGGER_URL`) are [ADR 0011](0011-devcontainer-worker-sidecars.md).

## Consequences

- CD can talk to Haystack RDS and request Bolt without waiting for an infra `sync-secrets` alias patch.
- Sync two-DB **hosts** stay in SM, not in the image or Haystack workflow YAML.
- Worker **commands** are [ADR 0011](0011-devcontainer-worker-sidecars.md). A green `verify` is still not proof that FDW merge or graph populate ran.
