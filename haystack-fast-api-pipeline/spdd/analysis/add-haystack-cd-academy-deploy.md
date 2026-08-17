# SPDD Analysis: add-haystack-cd-academy-deploy

**Companion:** [REASONS Canvas](../prompt/add-haystack-cd-academy-deploy.md)

## Problem

Branch 1 cannot load a CI image. Infra configure-only no longer composes Haystack.

## Strategy

Copy estate `guest_base` + `haystack`. resolve-image then Ansible `--limit haystack`. Verify SSM `:8000`.

## Success

`action=deploy` updates both guests. No Neo4j container. `verify` green if uvicorn answers.

`.env` aliases Postgres names the FastAPI app reads and sets `FLEET_BACKEND=sql` / `NEO4J_BACKEND=bolt` when SM omitted them. Sidecars use `uv run`. Missing app modules may crash-loop; that is not a verify failure. Operator checklist: `docs/PREPARE-HAYSTACK-REPO.md`.
