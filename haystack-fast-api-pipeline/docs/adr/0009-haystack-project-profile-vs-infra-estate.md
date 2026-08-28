# ADR 0009: Haystack Profile knobs live on the app project; estate URLs come from AWS

- **Status:** Accepted
- **Date:** 2026-08-18
- **Change:** `add-haystack-cd-academy-deploy` (env overlay)
- **Related:** [0004](0004-haystack-env-aliases-and-uv-sidecars.md), [0008](0008-haystack-ci-release-image-env-driven.md)
- **Infra ground truth:** estate `scripts/sync-secrets.sh` → `heavy-rental/haystack`

## Context

[`.env.example`](https://github.com/Heavy-Rental/haystack-fast-api/blob/develop/.env.example) lists product knobs (`NEED_DECOMPOSER`, `LLM_*`, `INDEXING_*`, `PRICING_SCHEMA`, `KG_*`). Putting those on infra `aws-infra-academy.yml` would mix VPC/RDS with product Profile A/B. Putting `NEO4J_URI` on the Haystack GitHub Environment would let someone set `bolt://neo4j:7687` and miss the Bolt NLB.

## Decision

| Owner | Keys |
| --- | --- |
| Infra `sync-secrets` (AWS) | `POSTGRES_*`, `DATABASE_URL`, `SOURCE_*`, `TARGET_*`, `NEO4J_URI` (Terraform `bolt://<nlb>:7687`), `NEO4J_USER` / `NEO4J_PASSWORD`, `NEO4J_POPULATE_URL` (`http://neo4j-populate:8089/v1/populate` — compose worker on `asg-haystack`, not an ALB), `FLEET_BACKEND=sql`, `NEO4J_BACKEND=bolt`, optional `LLM_API_KEY` |
| Haystack Environment `academy` or `AWS_ACTUAL` | `APP_NAME`, `APP_ENV`, `LOG_LEVEL`, `NEED_DECOMPOSER`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_TIMEOUT_SECONDS`, `LLM_TEMPERATURE`, listed `INDEXING_*` (including `INDEXING_ST_MODEL`), `IDEMPOTENCY_TTL_SECONDS`, `INDEXING_VIA_AGENT_GATE`, `PRICING_SCHEMA`, `NEO4J_BACKEND` (override only), `NEO4J_POPULATE_TIMEOUT_SECONDS`, `RECOMMEND_VIA_AGENT_GRAPH`, `RECOMMEND_FANOUT_CAP`, `KG_ARTIFACT_DIR`, `KG_APPLY_TRANSFORMS`, `PROJECT_AGENT_MODE`, `PROJECT_AGENT_TOP_K`, secret `LLM_API_KEY` |
| Release image `/app/.env` (from `.env.prod`) | Same product knobs as file defaults. **Not** estate URLs or secrets. Process env wins. |
| Never from the Haystack project | `NEO4J_URI`, `NEO4J_POPULATE_URL`, `POSTGRES_*`, `SOURCE_*`, `TARGET_*` |

Haystack CD overlays non-empty Environment values onto **guest** `.env` after SM map (academy or `AWS_ACTUAL`, whichever caller ran). Empty vars leave SM / image `/app/.env` / app defaults. The Release image never bakes these names as `ENV`/`ARG` (ADR 0008); it may ship a sanitized `.env.prod` as `/app/.env`. Setting a Profile variable does **not** rebuild GHCR or rewrite `/app/.env` inside the pulled tag. There is no Haystack CD Environment named `production` (academy caller is Vocareum-only, ADR 0001; paid is `AWS_ACTUAL`, ADR 0010). Sample: [`../samples/.env.prod`](../samples/.env.prod). Operator table: [`../BOOTSTRAP.md`](../BOOTSTRAP.md).

## Consequences

- Change Profile A/B with Haystack CD `configure-only`; no image rebuild; no infra `apply`. The same GHCR tag keeps its `/app/.env`; process env on the guest wins.
- Estate URL drift requires infra `configure-only` / `apply` so SM is rewritten.
- `NEO4J_POPULATE_URL` is not a public ALB. `:8089` stays on the Haystack host compose network.
