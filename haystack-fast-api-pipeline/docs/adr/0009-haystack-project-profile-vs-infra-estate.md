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
| Haystack Environment `academy` | `NEED_DECOMPOSER`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_TIMEOUT_SECONDS`, `LLM_TEMPERATURE`, listed `INDEXING_*`, `IDEMPOTENCY_TTL_SECONDS`, `INDEXING_VIA_AGENT_GATE`, `PRICING_SCHEMA`, `NEO4J_BACKEND` (override only), `NEO4J_POPULATE_TIMEOUT_SECONDS`, `RECOMMEND_VIA_AGENT_GRAPH`, `KG_ARTIFACT_DIR`, `KG_APPLY_TRANSFORMS`, secret `LLM_API_KEY` |
| Never from the Haystack project | `NEO4J_URI`, `NEO4J_POPULATE_URL`, `POSTGRES_*`, `SOURCE_*`, `TARGET_*` |

Haystack CD overlays non-empty Environment values onto guest `.env` after SM map. Empty vars leave SM / app defaults. The Release image never bakes these names (ADR 0008). There is no Haystack CD Environment named `production` (academy-only, ADR 0001).

## Consequences

- Change Profile A/B with Haystack CD `configure-only`; no image rebuild; no infra `apply`.
- Estate URL drift requires infra `configure-only` / `apply` so SM is rewritten.
- `NEO4J_POPULATE_URL` is not a public ALB. `:8089` stays on the Haystack host compose network.
