# Delta for haystack-cd-ansible (devcontainer workers)

## Purpose

CD compose must match estate ADR 0020 / Haystack ADR 0011. Live text also lives in [`add-haystack-cd-academy-deploy/specs/haystack-cd-ansible/spec.md`](../../../add-haystack-cd-academy-deploy/specs/haystack-cd-ansible/spec.md). This change **replaces** `uv run python -m …`.

## MODIFIED Requirements

### Requirement: Sidecar workers use estate scripts, not the uvicorn image
`postgres-haystack-sync` SHALL run `postgres:17` with `sync-from-primary.sh`. `neo4j-populate` SHALL run `python:3.12-slim` with `populate-neo4j-from-haystack.sh` (wraps `populate_neo4j.py`). Compose SHALL NOT use `python -m postgres_haystack_sync` or `python -m neo4j_populate`. Scripts SHALL be copied to `/opt/heavy-rental/workers/`. Verify SHALL still pass if those processes exit, as long as uvicorn answers on `:8000`. `:8089` SHALL NOT be published on a host or ALB port.

#### Scenario: Workers are not the Haystack API image
- GIVEN Haystack CD compose is written
- THEN `postgres-haystack-sync` image is `postgres:17`
- AND `neo4j-populate` image is `python:3.12-slim`
- AND `verify` is still green if `GET :8000/health` is 2xx

### Requirement: Worker credential aliases when SM omitted them
After SM → `.env`, the haystack role SHALL add aliases when the worker name is empty: `SOURCE_USER` / `SOURCE_PASSWORD` / `SOURCE_DB` from `POSTGRES_USERNAME` / `POSTGRES_PASSWORD` / `SOURCE_DATABASE`; `TARGET_USER` / `TARGET_PASSWORD` / `TARGET_DB` and `PG*` from `POSTGRES_*` / `TARGET_*`. It SHALL default `NEO4J_POPULATE_TRIGGER_URL` to `http://neo4j-populate:8089/v1/populate` when absent. It SHALL NOT invent `SOURCE_HOST` / `SOURCE_PORT` / `SOURCE_DATABASE` or `TARGET_HOST` / `TARGET_PORT` / `TARGET_DATABASE`.

#### Scenario: SOURCE_USER filled from Postgres username
- GIVEN `heavy-rental/haystack` has `POSTGRES_USERNAME` and no `SOURCE_USER`
- WHEN the haystack role writes `.env`
- THEN `.env` contains `SOURCE_USER` equal to `POSTGRES_USERNAME`
- AND `SOURCE_HOST` is still the SM SoR endpoint
