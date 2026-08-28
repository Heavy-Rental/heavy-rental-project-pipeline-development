# Design: Haystack CD Academy deploy

> **Later modified by** [`add-haystack-cd-workers`](../add-haystack-cd-workers/proposal.md) / [ADR 0011](../../../../docs/adr/0011-devcontainer-worker-sidecars.md).

## Context

`IMPLEMENTATION-PLAN.md` §6. Infra first-composes Haystack on `deploy-projects`. This CD re-runs `guest_base` + `haystack` only.

## Decisions

1. Copy estate roles; same three services (uvicorn `768m`/`1.0`, sync + populate `256m`/`0.25`, no `neo4j` service).
2. Image is a pipeline extra-var (`HAYSTACK_IMAGE` / `image_ref` / tar). Empty deploy and configure-only fail.
3. Public GHCR or ECR or tar. Private GHCR fails. No PAT on the guest.
4. Verify is SSM `GET :8000/health` (**2xx** only; same as ALB `tg-haystack` matcher `200-299`). No instance IPs or internal ALB in the summary.
5. After SM → `.env`, alias Postgres names the FastAPI app reads and set Academy live flags when SM omitted them (`FLEET_BACKEND=sql`, `NEO4J_BACKEND=bolt`). Overlay non-empty Haystack Environment `academy` Profile knobs onto the **guest** `.env` only (ADR 0009): `APP_NAME`, `APP_ENV`, `LOG_LEVEL`, `NEED_DECOMPOSER`, `LLM_*` (including `LLM_API_KEY`), `INDEXING_*` (including `INDEXING_ST_MODEL`), `IDEMPOTENCY_TTL_SECONDS`, `INDEXING_VIA_AGENT_GATE`, `FLEET_BACKEND`, `PRICING_SCHEMA`, `NEO4J_BACKEND`, `NEO4J_POPULATE_TIMEOUT_SECONDS`, `RECOMMEND_VIA_AGENT_GRAPH`, `RECOMMEND_FANOUT_CAP`, `KG_*`, `PROJECT_AGENT_*`. Empty vars leave SM / image `/app/.env`. Do not invent `LLM_API_KEY` when the Environment secret is empty. Do not overlay `NEO4J_URI`, `NEO4J_POPULATE_URL`, `NEO4J_USER`, `NEO4J_PASSWORD`, `POSTGRES_*`, `DATABASE_URL`, `SOURCE_*`, or `TARGET_*`. CD SHALL NOT rebuild the image or rewrite `/app/.env` inside the pulled tag.
6. Sidecar **runtime** later became estate/CD scripts (`postgres:17` / `python:3.12-slim`) — [ADR 0011](../../../../docs/adr/0011-devcontainer-worker-sidecars.md) / [`add-haystack-cd-workers`](../add-haystack-cd-workers/proposal.md). Missing uvicorn `-m` modules no longer apply. Verify still does not require workers to succeed.

## Risks

- Drift if estate `haystack` compose changes (copy `files/` + `compose.yml.j2` again).
- Old tag does not pull (`compose up` is not `--pull always`).
- Worker failure (FDW missing, NAT, Bolt) does not fail `verify`; a green `/health` is not proof that sync or populate ran.
