# Haystack app CD (Academy)

This workflow discovers `asg-haystack` and can re-run Haystack compose (branch 2). It does **not** run Terraform or create the ASG. It does **not** start Neo4j.

Specification index: [`../specification/README.md`](../specification/README.md). CD walkthrough: [`../specification/pipelines/haystack-cd.md`](../specification/pipelines/haystack-cd.md).

**App repo is not ready yet.** Checklist, image contract, sidecar gaps, and the full env-name table: [`PREPARE-HAYSTACK-REPO.md`](PREPARE-HAYSTACK-REPO.md). Production-shaped product knobs: [`samples/.env.prod`](samples/.env.prod).

Install from **`deploy-pipeline/`** into the Haystack app repo (same paths as PREPARE §4):

- `haystack-cd-academy-caller.yml` → `.github/workflows/`
- `haystack-cd-paid-caller.yml` → `.github/workflows/` (billed AWS)
- `haystack-cd-academy.yml` → `.github/workflows/` (shared jobs)
- `resolve-aws-profile/action.yml` → `.github/actions/resolve-aws-profile/`
- **`ansible/`** → `deploy-pipeline/ansible/` (keep this path)

Do **not** copy `specification/`. Copy [`samples/.env.prod`](samples/.env.prod) to the **app** repo as `.env.prod` so Release sanitizes it to `/app/.env`. pydantic `Settings` loads `.env` only; it does not auto-select `.env.prod`.

## Env ownership (same as PREPARE §7)

| Owner | Keys |
| --- | --- |
| Infra `sync-secrets` → `heavy-rental/haystack` | `POSTGRES_*`, `DATABASE_URL`, `SOURCE_*`, `TARGET_*`, Bolt NLB `NEO4J_URI` / `USER` / `PASSWORD`, `NEO4J_POPULATE_URL=http://neo4j-populate:8089/v1/populate`, `FLEET_BACKEND=sql`, `NEO4J_BACKEND=bolt`, optional `LLM_API_KEY` |
| Image `/app/.env` (sanitized `.env.prod`) | Product knobs (`APP_ENV=prod`, `NEED_DECOMPOSER`, `LLM_*` without the key, `INDEXING_*`, `KG_*`, …). **No** estate hosts or secrets. |
| Haystack Environment `academy` overlay | Non-empty Profile vars/secrets below. Empty = keep SM / image `/app/.env`. |

Compose `env_file` on the guest is the SM map (plus aliases and overlay). Process env **wins** over `/app/.env`. Haystack RDS database name is **`haystack`**. `SOURCE_DATABASE` is **`heavy_rental`**.

## GitHub Environment `academy`

This Environment is the Haystack **project** production-style config store (Vocareum). Infra still owns RDS hosts and Bolt NLB. Do **not** point CD at CI Environments `integration` or `production`.

## GitHub Environment `AWS_ACTUAL` (paid)

Create Environment **`AWS_ACTUAL`**. Variable `AWS_ROLE_TO_ASSUME` (OIDC). Same `HAYSTACK_IMAGE` and Profile overlay names. Optional secret `LLM_API_KEY`. **No** `AWS_ACCESS_KEY_ID`. Run **Haystack CD (paid)** after infra paid `apply`. Ansible SSM uses `heavy-rental-ssm-<account>-actual`. No neo4j container.

### Secrets (runner only — optional fallback)

| Secret | When required |
| --- | --- |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_SESSION_TOKEN` | If the Run form fields are empty. Never on the EC2 or in AWS Secrets Manager. |
| `LLM_API_KEY` | Overlay onto guest `.env` when set. Never on the Run form, never in `.env.prod`, never baked into the image. |

### Variables

| Variable | Required? | Role |
| --- | --- | --- |
| `AWS_REGION` | Recommended | Defaults to `us-east-1` if empty |
| `HAYSTACK_IMAGE` | Required for `deploy` / `configure-only` unless `image_ref` is set | Public GHCR or ECR tag. **No stock uvicorn.** |
| `IMAGE_HTTP_URL` | Optional | HTTPS or `s3://` CI `.tar.gz` for `docker load` |
| Profile knobs (optional) | Empty = keep SM / image `/app/.env` | **Not baked into the image.** See below. `APP_NAME`, `APP_ENV`, `LOG_LEVEL`, `NEED_DECOMPOSER`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_TIMEOUT_SECONDS`, `LLM_TEMPERATURE`, `INDEXING_EMBEDDER`, `INDEXING_EMBEDDING_DIM`, `INDEXING_SPLIT_LENGTH`, `INDEXING_SPLIT_OVERLAP`, `INDEXING_OPENAI_EMBEDDING_MODEL`, `INDEXING_ST_MODEL`, `INDEXING_DOCUMENT_STORE`, `INDEXING_CHUNK_TTL_SECONDS`, `IDEMPOTENCY_TTL_SECONDS`, `INDEXING_VIA_AGENT_GATE`, `FLEET_BACKEND`, `PRICING_SCHEMA`, `NEO4J_BACKEND`, `NEO4J_POPULATE_TIMEOUT_SECONDS`, `RECOMMEND_VIA_AGENT_GRAPH`, `RECOMMEND_FANOUT_CAP`, `KG_ARTIFACT_DIR`, `KG_APPLY_TRANSFORMS`, `PROJECT_AGENT_MODE`, `PROJECT_AGENT_TOP_K` |

### Setting a Profile variable does **not** change the Docker image

Academy Profile knobs are applied later, on the EC2, when this CD runs `deploy` or `configure-only`. Ansible writes non-empty values onto the **guest** `.env`. Compose injects that file as process environment. pydantic prefers process env over `/app/.env` already inside the image.

| When you set it | Where it lands | Rebuild image? |
| --- | --- | --- |
| GitHub Environment `academy` Profile variable (the list above) | Guest `.env` on `asg-haystack` at CD time | **No** |
| App repo `.env.prod`, then Release Packaging | Image `/app/.env` (product knobs only; estate keys stripped) | **Yes** — new GHCR tag |
| Infra `sync-secrets` | `heavy-rental/haystack` → guest `.env` (RDS, Bolt NLB, …) | **No** |

Empty academy vars leave whatever is already there: Secrets Manager, or the image `/app/.env` defaults from `.env.prod`.

Example: `NEED_DECOMPOSER=llm` on academy changes the **running** container after the next `configure-only` or `deploy`. It does **not** change `ghcr.io/…/haystack_recommender:<tag>`. The next guest that pulls the same tag still gets the image file defaults until CD overlays again.

`HAYSTACK_IMAGE` is only which tag to pull. It is not a Profile knob and is not copied into the image.

Do **not** set `NEO4J_URI`, `NEO4J_POPULATE_URL`, `NEO4J_USER`, `NEO4J_PASSWORD`, `POSTGRES_*`, `DATABASE_URL`, `SOURCE_*`, or `TARGET_*` here. CD will not overlay them. Infra writes Bolt NLB `NEO4J_URI` and `NEO4J_POPULATE_URL=http://neo4j-populate:8089/v1/populate` (compose worker on `asg-haystack`, not an ALB).

Infra must already have applied the estate and `sync-secrets` (`heavy-rental/haystack`). Guests InService + SSM Online. Desired=0 is infra, not this CD.

## Every run (same as PREPARE §10)

1. Instructure → Start Lab → AWS Details.
2. Actions → **Haystack CD (Academy)** → Environment `academy` → paste Vocareum keys (or Environment fallback).
3. `action=verify` — assert-lab + discover + SSM `GET :8000/docs` or `/health` (SoR/Bolt down does not fail this job by itself if uvicorn answers).
4. `action=deploy` — **new** public GHCR or ECR tag (or tar URL + matching tag). Prefer a **new tag** (`compose up` is not `--pull always`).
5. `action=configure-only` — refresh guest `.env` from `heavy-rental/haystack`, add Postgres aliases / `FLEET_BACKEND=sql` / `NEO4J_BACKEND=bolt` if missing, overlay non-empty academy Profile vars. Still needs `HAYSTACK_IMAGE` or `image_ref`. No stock uvicorn.

Sidecar crash-loops (`postgres-haystack-sync`, `neo4j-populate`) do **not** fail `verify` if uvicorn answers. A green verify is not proof that sync or populate ran.

The **runner** uses Vocareum keys. The **EC2** uses `LabRole`.

## Do not (same as PREPARE §11)

- Use CI Environments `integration` / `production` as CD
- Expect GHCR from a `develop` → `master` PR alone (run **Actions → Haystack Release Pipeline Invoke** after merge to `master`; that workflow creates the GitHub Release)
- Put Vocareum keys or `LLM_API_KEY` in the image, in `.env.prod`, or on the Run form
- Type instance IDs on the Run form
- Run `terraform apply` from this workflow
- Start a `neo4j` container on `asg-haystack`
- Set `NEO4J_URI=bolt://neo4j:7687` or a guest private IP
- Treat a green `verify` as proof that sync or populate ran
