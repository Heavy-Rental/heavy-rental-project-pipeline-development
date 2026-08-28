# SPDD Analysis: add-haystack-cd-workers

**Companion:** [REASONS Canvas](../prompt/add-haystack-cd-workers.md)

## Problem

CD compose still used `uv run python -m` on the uvicorn image (ADR 0004). Estate first-compose now uses Fast API devcontainer scripts on `postgres:17` / `python:3.12-slim` (infra ADR 0020). App packages are often absent, so workers crash-looped and SoR → Haystack RDS never ran. Leaving CD on `-m` would fork estate (ADR 0003).

## Strategy

Copy estate `files/` + `compose.yml.j2`. Alias missing worker credential names from existing SM keys. Do not invent `SOURCE_HOST` / `TARGET_HOST`. Verify stays `GET :8000/health` **2xx**.

## Success

`postgres-haystack-sync` image is `postgres:17`. `neo4j-populate` image is `python:3.12-slim`. Scripts are on `/opt/heavy-rental/workers/`. Worker failure does not fail `verify`. Operator docs name ADR 0011.
