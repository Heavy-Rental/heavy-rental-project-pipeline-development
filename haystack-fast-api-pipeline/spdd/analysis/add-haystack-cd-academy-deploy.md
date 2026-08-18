# SPDD Analysis: add-haystack-cd-academy-deploy

**Companion:** [REASONS Canvas](../prompt/add-haystack-cd-academy-deploy.md)

## Problem

Branch 1 cannot load a CI image. Infra configure-only no longer composes Haystack.

## Strategy

Copy estate `guest_base` + `haystack`. resolve-image then Ansible `--limit haystack`. Verify SSM `:8000`.

## Success

`action=deploy` updates both guests. No Neo4j container. `verify` green if uvicorn answers.

`.env` aliases Postgres names the FastAPI app reads and sets `FLEET_BACKEND=sql` / `NEO4J_BACKEND=bolt` when SM omitted them. Non-empty Haystack Environment `academy` Profile knobs (`APP_NAME`, `APP_ENV`, `NEED_DECOMPOSER`, `LLM_*`, `INDEXING_*` including `INDEXING_ST_MODEL`, `PROJECT_AGENT_*`, `RECOMMEND_FANOUT_CAP`, …) overlay the **guest** `.env` after that (ADR 0009). They do **not** rebuild GHCR or rewrite `/app/.env` in the image. Empty vars leave SM / image `/app/.env`. Do not overlay `NEO4J_URI` or `NEO4J_POPULATE_URL` (infra AWS). Sidecars use `uv run`. Missing app modules may crash-loop; that is not a verify failure. Operator: `docs/BOOTSTRAP.md`, `docs/PREPARE-HAYSTACK-REPO.md`, `docs/samples/.env.prod`.
