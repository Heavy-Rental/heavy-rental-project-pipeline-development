# Haystack app CD (Academy)

This workflow discovers `asg-haystack` and can re-run Haystack compose (branch 2). It does **not** run Terraform or create the ASG. It does **not** start Neo4j.

Specification index: [`../specification/README.md`](../specification/README.md). CD walkthrough: [`../specification/pipelines/haystack-cd.md`](../specification/pipelines/haystack-cd.md).

**App repo is not ready yet.** Checklist and env/sidecar gaps: [`PREPARE-HAYSTACK-REPO.md`](PREPARE-HAYSTACK-REPO.md).

Install from **`deploy-pipeline/`** into the Haystack app repo (same pattern as Release):

- `haystack-cd-academy-caller.yml` → `.github/workflows/`
- `haystack-cd-academy.yml` → `.github/workflows/`
- `resolve-vocareum-aws/action.yml` → `.github/actions/resolve-vocareum-aws/`
- **`ansible/`** → `deploy-pipeline/ansible/` (keep this path)

## GitHub Environment `academy`

This Environment is the Haystack **project** production-style config store (Vocareum). Infra still owns RDS hosts and Bolt NLB.

- Optional fallback secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`
- Optional secret: `LLM_API_KEY` — overlay onto guest `.env` when set. Never on the Run form.
- Variable: `AWS_REGION` = `us-east-1`
- Variable: `HAYSTACK_IMAGE` — public GHCR or ECR tag. **Required** for `deploy` / `configure-only` unless `image_ref` is set. No stock uvicorn.
- Optional: `IMAGE_HTTP_URL` — HTTPS or `s3://` CI tar
- Optional Profile variables (empty = keep SM / app `develop` defaults):  
  `NEED_DECOMPOSER`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_TIMEOUT_SECONDS`, `LLM_TEMPERATURE`,  
  `INDEXING_EMBEDDER`, `INDEXING_EMBEDDING_DIM`, `INDEXING_SPLIT_LENGTH`, `INDEXING_SPLIT_OVERLAP`,  
  `INDEXING_OPENAI_EMBEDDING_MODEL`, `INDEXING_DOCUMENT_STORE`, `INDEXING_CHUNK_TTL_SECONDS`,  
  `IDEMPOTENCY_TTL_SECONDS`, `INDEXING_VIA_AGENT_GATE`, `FLEET_BACKEND`, `PRICING_SCHEMA`,  
  `NEO4J_BACKEND`, `NEO4J_POPULATE_TIMEOUT_SECONDS`,  
  `RECOMMEND_VIA_AGENT_GRAPH`, `KG_ARTIFACT_DIR`, `KG_APPLY_TRANSFORMS`

Do **not** set `NEO4J_URI` or `NEO4J_POPULATE_URL` here. Infra writes Bolt NLB `NEO4J_URI` and `NEO4J_POPULATE_URL=http://neo4j-populate:8089/v1/populate` (compose worker on `asg-haystack`) into `heavy-rental/haystack`.

Infra must already have applied the estate and `sync-secrets` (`heavy-rental/haystack`).

## Every run

1. Start Lab → AWS Details.
2. Actions → **Haystack CD (Academy)** → Environment `academy` → paste Vocareum keys (or Environment fallback).
3. `action=verify` — assert + discover + SSM `GET :8000/docs` or `/health`.
4. `action=configure-only` — refresh `.env` from `heavy-rental/haystack`, add app aliases / live flags if missing, overlay Environment Profile vars; needs `HAYSTACK_IMAGE` or `image_ref`.
5. `action=deploy` — new public GHCR/ECR tag (or tar). Prefer a **new tag**. Sidecar crash-loops do not fail `verify` if uvicorn answers.

The **runner** uses Vocareum keys. The **EC2** uses `LabRole`.
