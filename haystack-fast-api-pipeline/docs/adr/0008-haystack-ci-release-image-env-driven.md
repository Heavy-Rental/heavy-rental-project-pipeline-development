# ADR 0008: Haystack Release image takes DB and sync config from the environment

- **Status:** Accepted
- **Date:** 2026-08-18
- **Change:** `add-haystack-ci-pipeline` (image contract)
- **Related:** [0004](0004-haystack-env-aliases-and-uv-sidecars.md) (CD injects SM), [0007](0007-haystack-ci-stops-at-packaging.md)

## Context

Academy compose reuses the Release image for uvicorn, `postgres-haystack-sync`, and `neo4j-populate`. Infra `sync-secrets` writes `POSTGRES_*` / `DATABASE_URL`, `SOURCE_*` (SoR / REST RDS), `TARGET_*` (Haystack RDS), and `NEO4J_*` into `heavy-rental/haystack`. Baking lab hostnames into the image would pin every tag to one estate.

## Decision

Release Packaging generates (or accepts) a Dockerfile with **no** `ENV`/`ARG` for those keys and no `.env` copy. After `docker build`, it inspects `Config.Env` and runs the image with **dummy** `SOURCE_*` / `TARGET_*` / `POSTGRES_*` / `DATABASE_URL` to prove they are visible. It does not connect to RDS. Sidecar packages are copied only if the checkout already has them.

## Consequences

- Same image tag works on any Academy lab once CD injects SM.
- An app `Dockerfile` that bakes `POSTGRES_HOST` fails Packaging.
- Missing `postgres_haystack_sync` is a warning, not a red Release (app `develop` still lacks the module).
