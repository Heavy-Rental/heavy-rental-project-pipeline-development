# Proposal: Haystack CD workers match estate devcontainer scripts

## Why

CD compose used `uv run python -m` (ADR 0004). Estate now uses Fast API devcontainer scripts on `postgres:17` / `python:3.12-slim` (infra ADR 0020). CD must copy that compose or first-compose and CD diverge (ADR 0003). App `develop` often lacks `postgres_haystack_sync` / `neo4j_populate`, so `-m` workers crash-looped and never synced.

## What Changes

- ADR 0011 amends 0004.
- Copy `files/` (`sync-from-primary.sh`, `populate_neo4j.py`, `populate-neo4j-from-haystack.sh`) + `compose.yml.j2` from estate haystack role.
- Alias worker credential names (`SOURCE_USER`, `TARGET_USER`, `PG*`, `NEO4J_POPULATE_TRIGGER_URL`) when SM omitted them. Do not invent `SOURCE_HOST` / `TARGET_HOST`.
- OpenSpec `haystack-cd-ansible` sidecar requirement describes `postgres:17` / `python:3.12-slim`, not uvicorn `-m`.

## Capabilities

### Modified Capabilities

- `haystack-cd-ansible`: workers are estate scripts, not uvicorn `-m`; worker env aliases

## Impact

- Copy `deploy-pipeline/ansible/roles/haystack/files/` into the app repo with the rest of `ansible/`.
- Verify remains `GET :8000/health` **2xx**. Worker failure does not fail the job.
