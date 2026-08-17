# ADR 0004: App env aliases and uv sidecar commands

- **Status:** Accepted
- **Date:** 2026-08-17
- **Change:** `add-haystack-cd-academy-deploy`
- **Amends:** [0003](0003-reuse-infra-haystack-ansible.md) (same three services; env post-process + sidecar entrypoint)

## Context

[Heavy-Rental/haystack-fast-api](https://github.com/Heavy-Rental/haystack-fast-api) `develop` reads `POSTGRES_HOSTNAME` / `POSTGRES_DB` / `POSTGRES_USER` and defaults `FLEET_BACKEND=fake`, `NEO4J_BACKEND=fake`. Infra `heavy-rental/haystack` writes `POSTGRES_HOST` / `DATABASE` / `USERNAME` and `NEO4J_URI` but not those live flags. The Release image uses `uv run`; estate compose used `python -m` (system Python, no venv).

## Decision

After `guest_base` maps SM → `.env`, the haystack role fills **missing** aliases and Academy live flags only. Sidecar commands are `uv run python -m postgres_haystack_sync` and `uv run python -m neo4j_populate`. Services, limits, and the no-`neo4j` check stay as estate. Ansible fails if uvicorn never answers; sidecar crash-loops do not fail `verify`.

## Consequences

- CD can talk to Haystack RDS and request Bolt without waiting for an infra `sync-secrets` alias patch.
- Sidecars still crash until the app ships those modules (see [`PREPARE-HAYSTACK-REPO.md`](../PREPARE-HAYSTACK-REPO.md)).
