# Design: Haystack CD Academy deploy

## Context

`IMPLEMENTATION-PLAN.md` §6. Infra first-composes Haystack on `apply`. This CD re-runs `guest_base` + `haystack` only.

## Decisions

1. Copy estate roles; same three services (uvicorn `768m`/`1.0`, sync + populate `256m`/`0.25`, no `neo4j` service).
2. Image is a pipeline extra-var (`HAYSTACK_IMAGE` / `image_ref` / tar). Empty deploy and configure-only fail.
3. Public GHCR or ECR or tar. Private GHCR fails. No PAT on the guest.
4. Verify is SSM `GET :8000/docs` or `/health`. No instance IPs or internal ALB in the summary.
5. After SM → `.env`, alias Postgres names the FastAPI app reads and set Academy live flags when SM omitted them (`FLEET_BACKEND=sql`, `NEO4J_BACKEND=bolt`). Do not invent `LLM_API_KEY`.
6. Sidecar commands are `uv run python -m …` so they share the Release image venv. Missing modules crash-loop; that does not fail `verify`.

## Risks

- Drift if estate `haystack` compose changes.
- Old tag does not pull (`compose up` is not `--pull always`).
- Live app (`develop` 2026-08-17) has no sidecar packages — sync/populate will not run until the app ships them.
