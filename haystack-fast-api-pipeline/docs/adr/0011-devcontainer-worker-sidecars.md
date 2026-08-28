# ADR 0011: CD Haystack workers match estate devcontainer scripts

- **Status:** Accepted
- **Date:** 2026-08-28
- **Change:** `add-haystack-cd-workers`
- **Amends:** [0004](0004-haystack-env-aliases-and-uv-sidecars.md)
- **Related:** [0003](0003-reuse-infra-haystack-ansible.md), infra ADR 0020 (`heavy-rental-project-instructure-and-cloud-deploy/docs/adr/0020-haystack-devcontainer-workers.md`)

## Context

ADR 0004 set sidecar commands to `uv run python -m postgres_haystack_sync` and `python -m neo4j_populate` on the Release image. Those packages are often absent; crash-loops did not fail `verify`. Infra now runs the Fast API **devcontainer** scripts on dedicated images (ADR 0020). CD compose that still used `-m` would fork estate (ADR 0003) and would not sync.

## Decision

Haystack CD copies estate:

1. Ansible copies `sync-from-primary.sh`, `populate_neo4j.py`, and `populate-neo4j-from-haystack.sh` to `/opt/heavy-rental/workers/`.
2. `postgres-haystack-sync` is public `postgres:17` + `sync-from-primary.sh`. `neo4j-populate` is public `python:3.12-slim` + `populate-neo4j-from-haystack.sh` (wraps `populate_neo4j.py`; pip-installs `psycopg[binary]==3.2.9` and `neo4j==5.28.1` at start). `restart: unless-stopped`. No guest `docker build`. No uvicorn `-m`.
3. `:8089` stays on the Compose network. It is not published on the host or Haystack ALB.
4. After SM → `.env`, fill **missing** worker names only: `SOURCE_USER` / `SOURCE_PASSWORD` / `SOURCE_DB` from `POSTGRES_USERNAME` / `POSTGRES_PASSWORD` / `SOURCE_DATABASE`; `TARGET_USER` / `TARGET_PASSWORD` / `TARGET_DB` and `PG*` from `POSTGRES_*` / `TARGET_*`; `SYNC_INTERVAL_SECONDS=60`, `POPULATE_INTERVAL_SECONDS=60`, `POPULATE_TRIGGER_MODE=both`, `POPULATE_HTTP_ENABLED=true`, `NEO4J_POPULATE_TRIGGER_URL=http://neo4j-populate:8089/v1/populate`. Do **not** invent `SOURCE_HOST` / `SOURCE_PORT` / `SOURCE_DATABASE` or `TARGET_HOST` / `TARGET_PORT` / `TARGET_DATABASE`. Overlay still must not write `NEO4J_URI` / `NEO4J_POPULATE_URL` / `POSTGRES_*` / `SOURCE_*` / `TARGET_*`.
5. Verify remains SSM `GET :8000/health` **2xx**. Worker failure does not fail `verify`.

## Alternatives

1. **Leave CD on `-m`.** Rejected: first-compose and CD would diverge; workers would still crash without app modules.

## Consequences

- Copy `files/` and `compose.yml.j2` when estate Haystack workers change.
- First-compose / CD needs NAT to pull `postgres:17` and `python:3.12-slim`, plus `postgres_fdw` on Haystack RDS.
- A green `verify` is still not proof that FDW merge or graph populate succeeded.
