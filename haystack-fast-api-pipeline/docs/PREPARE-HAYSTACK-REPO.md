# Prepare haystack-fast-api for Academy CD

**App repo:** [Heavy-Rental/haystack-fast-api](https://github.com/Heavy-Rental/haystack-fast-api)  
**Checked (point-in-time snapshot, not live inventory):** `develop` @ `a25128cb` (2026-08-17), open [PR #99](https://github.com/Heavy-Rental/haystack-fast-api/pull/99) (`HR-155`)  
**Release CI:** `release-pipeline/` in this tree — **not** on app `develop` / `master`. Packaging sanitizes `.env.prod` → `/app/.env`.  
**App CD:** `deploy-pipeline/` (this tree — **not** in the app repo yet)  
**Estate:** infra `apply` + `sync-secrets` must have created `asg-haystack` and `heavy-rental/haystack`

This file is the operator checklist and readiness record. It does not apply Terraform, merge the app PR, or push images.

**Verdict: not ready to deploy today.** The FastAPI process matches the image contract. The live repo cannot yet produce a pullable GHCR image (Release is not on `develop` / `master`). Compose workers no longer need app `postgres_haystack_sync` / `neo4j_populate` packages — CD copies estate scripts onto `postgres:17` / `python:3.12-slim` (ADR 0011). Product knobs ship as `/app/.env` from sanitized `.env.prod`; estate URLs still require infra `sync-secrets`. CD overlays academy / `AWS_ACTUAL` Profile vars onto guest `.env` after SM (see [`BOOTSTRAP.md`](BOOTSTRAP.md)).

Everyday operate after install (academy inventory, every-run steps, do-nots): [`BOOTSTRAP.md`](BOOTSTRAP.md). Specification: [`../specification/pipelines/haystack-cd.md`](../specification/pipelines/haystack-cd.md). Sample product file: [`samples/.env.prod`](samples/.env.prod).

---

## 1. Can Release build the image CD expects?

**The app source matches. Release is not on `develop`, so no image exists yet.**

| App (`develop`) | Release / CD contract |
| --- | --- |
| Python **3.12**, `uv.lock`, `pyproject.toml`, `app/main.py` | `python:3.12-slim-bookworm` + uv + uvicorn `app.main:app` |
| `GET /docs`, `GET /health` on **`:8000`** | ALB `tg-haystack` waits for `GET <instance>:8000/health` **2xx** (matcher `200-299`). `/docs` is OpenAPI only. `/health` returns 200 even if Postgres is down (`status=degraded`) |
| App `Dockerfile` ignored | Release **always** generates the slim-bookworm + uvicorn image. Runnable with `docker run -p 8000:8000 -e …` (Docker Desktop or any Engine) |
| Pricing artifacts under `app/services/pricing/artifacts/` | Copied with `COPY app ./app` |

Generated image (app Dockerfile is ignored):

```dockerfile
# Runtime estate keys from heavy-rental/haystack (do not ENV/ARG these):
#   DATABASE_URL, POSTGRES_*, SOURCE_* (SoR), TARGET_* (Haystack RDS), NEO4J_*
# Product knobs: sanitized .env.prod → /app/.env (pydantic Settings).
FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --extra neo4j
COPY app ./app
COPY haystack.prod.env .env
# COPY postgres_haystack_sync / neo4j_populate only if those dirs exist in the checkout
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Packaging fails if the generated Dockerfile bakes `ENV`/`ARG` for infra `heavy-rental/haystack` keys or Profile knobs, or `COPY`s a raw `.env` / `.env.prod`. It **does** sanitize app `.env.prod` (or `docs/samples/.env.prod`, or generated production defaults), strip estate keys and secrets, and `COPY haystack.prod.env .env` so pydantic loads `APP_ENV=prod` and the other product knobs. After build it proves `Settings().app_env` comes from `/app/.env`, that `docker run -e` still overrides the file, that dummy SM names are visible, then starts uvicorn and requires `GET /docs` or `GET /health` on `:8000` (200–302). `/health` may be `degraded` without Postgres. It does not connect to RDS or an LLM.

Desktop / any Engine: `docker run -p 8000:8000 -e DATABASE_URL=… ghcr.io/<owner>/haystack_recommender:<tag>` — product knobs already come from `/app/.env`. Academy: infra `sync-secrets` → guest `.env` → compose `env_file` (process env wins over the image file).

Operator checklist for the file: [`samples/.env.prod`](samples/.env.prod). Copy it to the **app** repo as `.env.prod` (repo root) so Packaging uses your values instead of generated defaults. Do not put RDS hosts, `NEO4J_URI=bolt://neo4j:7687`, or `LLM_API_KEY` in that file.

GHCR name: `ghcr.io/<owner>/haystack_recommender` (lowercase). On `Heavy-Rental` that is `ghcr.io/heavy-rental/haystack_recommender:<x.y.z>` and `:latest`. The version tag is the previous GHCR semver with the patch bumped (first publish is `1.0.0`).

| Release trigger | What you get |
| --- | --- |
| **workflow_dispatch** (**Haystack Release Pipeline Invoke**) | Wheel/sdist + docker tar + DAST, then Publish pushes GHCR `<version>` + `:latest` and creates the GitHub Release |

Academy guests pull **public** GHCR with no token. A `develop` → `master` PR does **not** run Release. You need this dispatch (or `docker load` the tar via `image_http_url` / `IMAGE_HTTP_URL`, or copy the image to ECR).

`DEFAULT_APP_REPOSITORY: Heavy-Rental/haystack-fast-api` in the reusable YAML is correct. When Release runs **in** the app repo, checkout is the calling repo (into `app/`). That is correct.

Release’s generated image runs `uv sync --frozen --no-dev --extra neo4j` so Bolt has a driver. If the app adds its own `Dockerfile`, it must include that extra (or move `neo4j` into main deps).

---

## 2. Already on the app repo vs still to copy

| Ref | Fast Feedback | Integration | Release | App CD |
| --- | --- | --- | --- | --- |
| `develop` (default) | Missing | Missing | Missing | Missing |
| `master` | Missing | Missing | Missing | Missing |
| `HR-155` / [PR #99](https://github.com/Heavy-Rental/haystack-fast-api/pull/99) (open) | Present | Present | Present | **Missing** |

Zero GitHub Releases. Zero GHCR packages for this repo (checked 2026-08-17).

---

## 3. Produce a pullable image

1. Merge HR-155 (or copy Fast Feedback + Integration + Release onto `develop`).
2. Merge to `master`, then run **Actions → Haystack Release Pipeline Invoke → Run workflow**. That checks out `master`, runs QC + Packaging + DAST, then Publish pushes public GHCR and creates the GitHub Release.
3. Org Packages → `haystack_recommender` → visibility **Public**. Private GHCR fails CD on purpose (no PAT on the guest).
4. Record the tag, for example `ghcr.io/heavy-rental/haystack_recommender:1.0.0` (or `:latest`). Prefer a **new** version tag each deploy (`compose up` is not `--pull always`).

Optional Academy path: upload the Release tar to lab S3 and set `IMAGE_HTTP_URL` / `image_http_url` (`s3://` or HTTPS). You still need a compose tag that matches the loaded image name (`HAYSTACK_IMAGE` or `image_ref`).

---

## 4. Install Haystack app CD into the app repo

Copy from this tree’s `deploy-pipeline/`:

| Source | Destination in haystack-fast-api |
| --- | --- |
| `haystack-cd-academy-caller.yml` | `.github/workflows/` |
| `haystack-cd-paid-caller.yml` | `.github/workflows/` (billed AWS / OIDC) |
| `haystack-cd-academy.yml` | `.github/workflows/` (shared jobs) |
| `resolve-aws-profile/action.yml` | `.github/actions/resolve-aws-profile/` |
| `ansible/` | **`deploy-pipeline/ansible/`** (keep this path) |
| [`docs/samples/.env.prod`](samples/.env.prod) | **`.env.prod`** at the app repo root (Release sanitizes this to `/app/.env`) |

Do **not** copy `specification/`. Do **not** copy `resolve-vocareum-aws/` (unused; academy masking is inside `resolve-aws-profile`). Everyday operate after this copy: [`BOOTSTRAP.md`](BOOTSTRAP.md) (same CD files and the same academy inventory).

---

## 5. GitHub Environment `academy`

Create Environment **`academy`** on the Haystack repo. Do **not** point CD at CI Environments `integration` or `production`. Same inventory as [`BOOTSTRAP.md`](BOOTSTRAP.md).

### Secrets (runner only — optional fallback)

Paste Vocareum AWS Details on each Run after Start Lab, **or** store these as Environment secrets. They change every session. Never put them on the EC2 or in AWS Secrets Manager.

| Secret | When required |
| --- | --- |
| `AWS_ACCESS_KEY_ID` | If the Run form fields are empty |
| `AWS_SECRET_ACCESS_KEY` | If the Run form fields are empty |
| `AWS_SESSION_TOKEN` | If the Run form fields are empty |
| `LLM_API_KEY` | Optional overlay onto guest `.env`. Never on the Run form, never in `.env.prod`, never baked into the image. |

### Variables (not secrets)

| Variable | Required? | Role |
| --- | --- | --- |
| `AWS_REGION` | Recommended | Defaults to `us-east-1` if empty |
| `HAYSTACK_IMAGE` | Required for `deploy` / `configure-only` unless `image_ref` is set | Public GHCR or ECR tag. **No stock uvicorn.** |
| `IMAGE_HTTP_URL` | Optional | HTTPS or `s3://` CI `.tar.gz` for `docker load` |
| `APP_NAME`, `APP_ENV`, `LOG_LEVEL` | Optional | Overlay; empty keeps image `/app/.env` (`haystack-fast-api` / `prod` / `INFO`) |
| `NEED_DECOMPOSER`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_TIMEOUT_SECONDS`, `LLM_TEMPERATURE` | Optional | Overlay; empty keeps image `/app/.env`. Pair `NEED_DECOMPOSER=llm` with secret `LLM_API_KEY` |
| `INDEXING_EMBEDDER`, `INDEXING_EMBEDDING_DIM`, `INDEXING_SPLIT_LENGTH`, `INDEXING_SPLIT_OVERLAP`, `INDEXING_OPENAI_EMBEDDING_MODEL`, `INDEXING_ST_MODEL`, `INDEXING_DOCUMENT_STORE`, `INDEXING_CHUNK_TTL_SECONDS` | Optional | Overlay; empty keeps image `/app/.env` (mock / memory). `pgvector` still needs `CREATE EXTENSION vector` |
| `IDEMPOTENCY_TTL_SECONDS`, `INDEXING_VIA_AGENT_GATE` | Optional | Overlay; empty keeps image `/app/.env` |
| `FLEET_BACKEND`, `PRICING_SCHEMA`, `NEO4J_BACKEND` | Optional | Overlay only. Infra SM already writes `sql` / `bolt` if missing |
| `NEO4J_POPULATE_TIMEOUT_SECONDS` | Optional | Overlay; empty keeps image `/app/.env` (`2`). **Not** `NEO4J_POPULATE_URL` |
| `RECOMMEND_VIA_AGENT_GRAPH`, `RECOMMEND_FANOUT_CAP`, `KG_ARTIFACT_DIR`, `KG_APPLY_TRANSFORMS`, `PROJECT_AGENT_MODE`, `PROJECT_AGENT_TOP_K` | Optional | Overlay; empty keeps image `/app/.env` |

Do **not** set `NEO4J_URI`, `NEO4J_POPULATE_URL`, `NEO4J_USER`, `NEO4J_PASSWORD`, `POSTGRES_*`, `DATABASE_URL`, `SOURCE_*`, or `TARGET_*` on this Environment. CD will not overlay them.

### Run form

| Input | Use |
| --- | --- |
| `aws_environment` | Must be **`academy`** |
| `aws_access_key_id` / `aws_secret_access_key` / `aws_session_token` | Fresh Vocareum keys (override Environment secrets) |
| `image_ref` | One-off tag if `HAYSTACK_IMAGE` is empty |
| `image_http_url` | One-off tar if `IMAGE_HTTP_URL` is empty |

**Minimum `verify`:** Environment `academy` + three Vocareum keys + `AWS_REGION`.  
**Minimum `deploy` / `configure-only`:** that, plus `HAYSTACK_IMAGE` or `image_ref` (or a tar **and** a matching tag).

### Paid Environment `AWS_ACTUAL`

Create Environment **`AWS_ACTUAL`**. Variable `AWS_ROLE_TO_ASSUME` (OIDC). **No** Vocareum `AWS_*` secrets. Same `HAYSTACK_IMAGE` / `IMAGE_HTTP_URL` / `AWS_REGION` and Profile overlay names as academy, on **this** Environment. Optional secret `LLM_API_KEY`. Run **Haystack CD (paid)** after infra paid `apply`. Guests use `hr-paid-haystack`. Ansible SSM uses `heavy-rental-ssm-<account>-actual`. No neo4j container. Workers are the same ADR 0011 scripts.

---

## 6. AWS (infra, not GitHub)

This CD does **not** create the ASG or start Neo4j. Before any `deploy`:

1. Infra `action=apply` created `asg-haystack` (internal ALB `:8000`), Haystack RDS, Bolt NLB, `asg-neo4j`. Infra `apply` does **not** compose Haystack.
2. Infra `sync-secrets` filled **`heavy-rental/haystack`**.
3. Guests are InService and SSM Online (Start Lab if the session ended). Desired=0 → infra, not this CD.
4. First-compose is infra `deploy-projects` (`site.yml`) or this CD `action=deploy`.

The guest (`LabRole` on academy; `hr-paid-haystack` on paid) reads `heavy-rental/haystack`. `LLM_API_KEY` is never on the Run form, never in `.env.prod`, and never baked into the image (Haystack Environment secret or infra SM only).

---

## 7. Runtime env names (image can be right; keys may not)

App `Settings` (`app/config.py`) uses different names. Code defaults are still CI-safe (`fake` / `memory` / `stub`). The Release image `/app/.env` (from `.env.prod`) and infra SM override those. `DATABASE_URL` from SM wins for Postgres and is rewritten `postgresql://` → `postgresql+psycopg://`.

**Owner** (same three layers as [`BOOTSTRAP.md`](BOOTSTRAP.md)): infra `sync-secrets` writes estate names the app reads. The image ships product knobs in `/app/.env`. Haystack CD fills **missing** Postgres aliases, worker credential aliases, and `sql` / `bolt` after SM → guest `.env`, then overlays non-empty Haystack Environment Profile vars (`academy` or `AWS_ACTUAL`). It does not overwrite a value already in the secret unless the overlay sets that key.

| App reads | `heavy-rental/haystack` after the SM patch | CD `.env` if SM omitted the key |
| --- | --- | --- |
| `DATABASE_URL` | written (`postgresql://…/haystack`) | kept |
| `POSTGRES_HOSTNAME` | written (same as `POSTGRES_HOST`) | aliased from `POSTGRES_HOST` |
| `POSTGRES_DB` | written (same as `POSTGRES_DATABASE`) | aliased from `POSTGRES_DATABASE` |
| `POSTGRES_USER` | written (same as `POSTGRES_USERNAME`) | aliased from `POSTGRES_USERNAME` |
| `POSTGRES_PASSWORD` / `POSTGRES_PORT` | written | kept |
| `FLEET_BACKEND` | **`sql`** | set `sql` if absent |
| `NEO4J_BACKEND` | **`bolt`** | set `bolt` if absent |
| `NEO4J_URI` / `USER` / `PASSWORD` | written (NLB, not `bolt://neo4j:7687`) | kept |
| `INDEXING_DOCUMENT_STORE` | not written → image `/app/.env` **`memory`** | Haystack Environment overlay if set; **not** flipped by CD aliases (pgvector is optional) |
| `APP_NAME` / `APP_ENV` / `LOG_LEVEL` | not written | image `/app/.env` (`prod` / `INFO`); Haystack Environment overlay if set |
| `NEED_DECOMPOSER` | not written → image `/app/.env` **`stub`** | Haystack Environment `NEED_DECOMPOSER` overlays if set |
| `LLM_API_KEY` | optional on infra SM | Haystack Environment secret overlays if set; never invented; never in `.env.prod` |
| `LLM_BASE_URL` / `LLM_MODEL` / `LLM_TIMEOUT_SECONDS` / `LLM_TEMPERATURE` | not written → image `/app/.env` | Haystack Environment overlay or `docker -e` |
| `INDEXING_EMBEDDER` / `INDEXING_EMBEDDING_DIM` / `INDEXING_SPLIT_*` / `INDEXING_OPENAI_EMBEDDING_MODEL` / `INDEXING_ST_MODEL` / `INDEXING_CHUNK_TTL_SECONDS` | not written → image `/app/.env` (mock / 384 / …) | Haystack Environment overlay or `docker -e` |
| `IDEMPOTENCY_TTL_SECONDS` / `INDEXING_VIA_AGENT_GATE` | not written → image `/app/.env` | Haystack Environment overlay if set |
| `PRICING_SCHEMA` | not written → image `/app/.env` `primary_snapshot` | Haystack Environment overlay (`public` for live Spring tables) |
| `NEO4J_POPULATE_URL` | **`http://neo4j-populate:8089/v1/populate`** (compose worker on `asg-haystack`) | **not** overlaid; infra SM owns it; stripped from `.env.prod` |
| `NEO4J_POPULATE_TIMEOUT_SECONDS` | not written → image `/app/.env` `2` | Haystack Environment overlay if set |
| `RECOMMEND_VIA_AGENT_GRAPH` / `RECOMMEND_FANOUT_CAP` / `KG_ARTIFACT_DIR` / `KG_APPLY_TRANSFORMS` | not written → image `/app/.env` | Haystack Environment overlay or `docker -e` |
| `PROJECT_AGENT_MODE` / `PROJECT_AGENT_TOP_K` | not written → image `/app/.env` (`stub` / `5`) | Haystack Environment overlay if set |
| `SOURCE_HOST` / `SOURCE_PORT` / `SOURCE_DATABASE` | written (SoR / REST RDS `heavy_rental`) | **not** invented by CD |
| `SOURCE_USER` / `SOURCE_PASSWORD` / `SOURCE_DB` | not written | aliased from `POSTGRES_USERNAME` / `POSTGRES_PASSWORD` / `SOURCE_DATABASE` |
| `TARGET_HOST` / `TARGET_PORT` / `TARGET_DATABASE` | written (Haystack RDS — same host as `POSTGRES_*`) | **not** invented by CD |
| `TARGET_USER` / `TARGET_PASSWORD` / `TARGET_DB` / `PG*` | not written | aliased from `POSTGRES_*` / `TARGET_*` |
| `NEO4J_POPULATE_TRIGGER_URL` | optional | default `http://neo4j-populate:8089/v1/populate` if SM omitted it |

`postgres-haystack-sync` copies SoR → Haystack RDS using `SOURCE_*` / `TARGET_*` from `heavy-rental/haystack`. Infra `sync-secrets` owns the **hosts**. Haystack CD maps the secret to `.env`, aliases worker credential names (`SOURCE_USER`, `TARGET_USER`, `PG*`, …) when SM omitted them, and must **not** invent hosts, invent a third database, or copy `heavy-rental/rest`. There is no separate `SOURCE_USER` / `SOURCE_PASSWORD` in SM today — CD aliases `POSTGRES_USERNAME` / `POSTGRES_PASSWORD` (same Academy master password on both RDS instances).

Re-run infra `configure-only` (or `apply`) so SM is rewritten. Infra `deploy-projects` or Haystack CD then sees `sql` / `bolt` without waiting for a second overlay.

Haystack RDS database name is **`haystack`**, not the app example `heavy_rental`. `DATABASE_URL` from SM is the source of truth for uvicorn. `SOURCE_DATABASE` is **`heavy_rental`**.

`INDEXING_DOCUMENT_STORE=pgvector` still needs `CREATE EXTENSION vector` on Haystack RDS (infra `rds_logical`) and a matching `INDEXING_EMBEDDING_DIM`. Set `INDEXING_DOCUMENT_STORE` (and dim) on the Haystack Environment (`academy` or `AWS_ACTUAL`), then run Haystack CD `configure-only` — do not put that in infra `sync-secrets`.

Profile knobs (`APP_ENV`, `NEED_DECOMPOSER`, `LLM_*`, `INDEXING_*`, `PRICING_SCHEMA`, `KG_*`, …) ship as image `/app/.env` from `.env.prod` and may be overlaid from the Haystack Environment (`academy` or `AWS_ACTUAL`). Infra still owns hosts, Bolt NLB `NEO4J_URI`, and RDS passwords. pydantic does **not** auto-load a file named `.env.prod`; Release copies the sanitized file to `.env`.

---

## 8. Compose workers vs the live app

CD / estate compose (no `neo4j` service):

| Service | Limits | Runtime |
| --- | --- | --- |
| `haystack` (uvicorn) | `768m` / `1.0` | Haystack Release image `CMD` (`uv run uvicorn … :8000`) |
| `postgres-haystack-sync` | `256m` / `0.25` | `postgres:17` + `sync-from-primary.sh` (`unless-stopped`, 60s) |
| `neo4j-populate` | `256m` / `0.25` | `python:3.12-slim` + `populate_neo4j.py` (`unless-stopped`, 60s + Compose `:8089`) |

Scripts are copied from this CD / estate Ansible `files/` (Fast API `.devcontainer`). They are **not** `python -m` on the uvicorn image (ADR 0011). App `develop` missing those Python packages no longer blocks the workers.

The app’s optional populate hook is still HTTP on the Compose network:

- `NEO4J_POPULATE_URL` = `http://neo4j-populate:8089/v1/populate`
- `trigger_neo4j_populate` POSTs that URL
- Compose does **not** publish `:8089` (no SG 8089)

Do not start a `neo4j` container on `asg-haystack`.

---

## 9. What a forced `action=deploy` would do

1. **Today, on the app repo:** fail immediately — no CD workflow, no `HAYSTACK_IMAGE`, no GHCR tag.
2. **After copy + public image:** uvicorn can start; `/health` can pass; aliases + `FLEET_BACKEND=sql` + `NEO4J_BACKEND=bolt` are on `.env`; workers run on `postgres:17` / `python:3.12-slim` (need NAT + `postgres_fdw` on Haystack RDS). Uvicorn does not need a `neo4j` extra for the populate worker.

A green `/health` is still not proof that FDW merge or graph populate succeeded.

---

## 10. First CD run

Same sequence as [`BOOTSTRAP.md`](BOOTSTRAP.md) “Every run”:

1. Instructure → Start Lab → AWS Details.
2. Actions → **Haystack CD (Academy)** → Environment `academy` → paste the three keys (or use Environment fallback).
3. `action=verify` — assert-lab + discover + SSM `GET :8000/health` must be **2xx** (same as ALB `tg-haystack` matcher `200-299`). SoR/Bolt down does not fail this job by itself if `/health` is 2xx.
4. `action=deploy` with a **new** public GHCR or ECR tag (or tar URL + matching tag). Prefer a **new tag**.
5. `action=configure-only` refreshes guest `.env` from `heavy-rental/haystack`, adds Postgres aliases / `FLEET_BACKEND=sql` / `NEO4J_BACKEND=bolt` if missing, overlays non-empty academy Profile vars (still needs `HAYSTACK_IMAGE` or `image_ref` — no stock uvicorn).

Worker failures do not fail `verify` if uvicorn answers. A green verify is not proof that sync or populate ran.

---

## 11. Do not

- Use CI Environments `integration` / `production` as CD
- Expect GHCR from HR-155 or a `develop` → `master` PR alone (run **Haystack Release Pipeline Invoke**; that workflow creates the GitHub Release)
- Put Vocareum keys or `LLM_API_KEY` in the image, in `.env.prod`, or on the Run form
- Type instance IDs on the Run form
- Run `terraform apply` from this workflow
- Start a `neo4j` container on `asg-haystack`
- Set `NEO4J_URI=bolt://neo4j:7687` or a guest private IP
- Treat a green `verify` as proof that sync or populate ran
