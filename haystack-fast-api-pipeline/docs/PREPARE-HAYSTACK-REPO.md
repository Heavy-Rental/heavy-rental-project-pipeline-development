# Prepare haystack-fast-api for Academy CD

**App repo:** [Heavy-Rental/haystack-fast-api](https://github.com/Heavy-Rental/haystack-fast-api)  
**Checked:** `develop` @ `a25128cb` (2026-08-17), open [PR #99](https://github.com/Heavy-Rental/haystack-fast-api/pull/99) (`HR-155`)  
**Release CI:** `release-pipeline/` in this tree — **not** on app `develop` / `master`  
**App CD:** `deploy-pipeline/` (this tree — **not** in the app repo yet)  
**Estate:** infra `apply` + `sync-secrets` must have created `asg-haystack` and `heavy-rental/haystack`

This file is the operator checklist and readiness record. It does not apply Terraform, merge the app PR, or push images.

**Verdict: not ready to deploy today.** The FastAPI process matches the image contract. The live repo cannot yet produce a pullable GHCR image, cannot run the compose sidecars, and would stay on CI-safe fake/memory backends unless CD rewrites `.env` (this pipeline now does that).

Everyday operate after install: [`BOOTSTRAP.md`](BOOTSTRAP.md). Specification: [`../specification/pipelines/haystack-cd.md`](../specification/pipelines/haystack-cd.md).

---

## 1. Can Release build the image CD expects?

**The app source matches. Release is not on `develop`, so no image exists yet.**

| App (`develop`) | Release / CD contract |
| --- | --- |
| Python **3.12**, `uv.lock`, `pyproject.toml`, `app/main.py` | `python:3.12-slim-bookworm` + uv + uvicorn `app.main:app` |
| `GET /docs`, `GET /health` on **`:8000`** | Health `GET :8000/docs` or `/health` (200–302). `/health` returns 200 even if Postgres is down (`status=degraded`) |
| App `Dockerfile` ignored | Release **always** generates the slim-bookworm + uvicorn image. Runnable with `docker run -p 8000:8000 -e …` (Docker Desktop or any Engine) |
| Pricing artifacts under `app/services/pricing/artifacts/` | Copied with `COPY app ./app` |

Generated image (app Dockerfile is ignored):

```dockerfile
# Runtime env from heavy-rental/haystack (do not ENV/ARG these):
#   DATABASE_URL, POSTGRES_*, SOURCE_* (SoR), TARGET_* (Haystack RDS), NEO4J_*
FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --extra neo4j
COPY app ./app
# COPY postgres_haystack_sync / neo4j_populate only if those dirs exist in the checkout
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Packaging fails if the generated Dockerfile bakes `ENV`/`ARG` for infra `heavy-rental/haystack` keys or `.env.example` knobs (`NEED_DECOMPOSER`, `LLM_*`, `INDEXING_*`, `IDEMPOTENCY_*`, `FLEET_BACKEND`, `PRICING_SCHEMA`, `NEO4J_*`, `RECOMMEND_VIA_AGENT_GRAPH`, `KG_*`) or copies a `.env`. After build it proves dummy values for those names are visible, then starts uvicorn and requires `GET /docs` or `GET /health` on `:8000` (200–302). `/health` may be `degraded` without Postgres. It does not connect to RDS or an LLM.

Desktop / any Engine: `docker run -p 8000:8000 -e DATABASE_URL=… -e FLEET_BACKEND=sql … ghcr.io/<owner>/haystack_recommender:<tag>`. Academy: infra `sync-secrets` → guest `.env` → compose `env_file`.

GHCR name: `ghcr.io/<owner>/haystack_recommender` (lowercase). On `Heavy-Rental` that is `ghcr.io/heavy-rental/haystack_recommender:<x.y.z>` and `:latest`. The version tag is the previous GHCR semver with the patch bumped (first publish is `1.0.0`).

| Release trigger | What you get |
| --- | --- |
| PR `develop` → `master` | Versioned wheel/sdist + docker **tar artifact**. **No GHCR push.** |
| **Published GitHub Release** | Tar **and** GHCR `<version>` + `:latest` |

Academy guests pull **public** GHCR with no token. A PR build is not enough for `HAYSTACK_IMAGE=ghcr.io/…` unless you `docker load` the tar (`image_http_url` / `IMAGE_HTTP_URL`) or copy the image to ECR.

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
2. Merge to `master` and **publish a GitHub Release**. That is what pushes GHCR.
3. Org Packages → `haystack_recommender` → visibility **Public**. Private GHCR fails CD on purpose (no PAT on the guest).
4. Record the tag, for example `ghcr.io/heavy-rental/haystack_recommender:1.0.0` (or `:latest`). Prefer a **new** version tag each deploy (`compose up` is not `--pull always`).

Optional Academy path: upload the Release tar to lab S3 and set `IMAGE_HTTP_URL` / `image_http_url` (`s3://` or HTTPS). You still need a compose tag that matches the loaded image name (`HAYSTACK_IMAGE` or `image_ref`).

---

## 4. Install Haystack app CD into the app repo

Copy from this tree’s `deploy-pipeline/`:

| Source | Destination in haystack-fast-api |
| --- | --- |
| `haystack-cd-academy-caller.yml` | `.github/workflows/` |
| `haystack-cd-academy.yml` | `.github/workflows/` |
| `resolve-vocareum-aws/action.yml` | `.github/actions/resolve-vocareum-aws/` |
| `ansible/` | **`deploy-pipeline/ansible/`** (keep this path) |

Do **not** copy `specification/`. Everyday operate: [`BOOTSTRAP.md`](BOOTSTRAP.md).

---

## 5. GitHub Environment `academy`

Create Environment **`academy`** on the Haystack repo. Do **not** point CD at CI Environments `integration` or `production`.

### Secrets (runner only — optional fallback)

Paste Vocareum AWS Details on each Run after Start Lab, **or** store these as Environment secrets. They change every session. Never put them on the EC2 or in AWS Secrets Manager.

| Secret | When required |
| --- | --- |
| `AWS_ACCESS_KEY_ID` | If the Run form fields are empty |
| `AWS_SECRET_ACCESS_KEY` | If the Run form fields are empty |
| `AWS_SESSION_TOKEN` | If the Run form fields are empty |

### Variables (not secrets)

| Variable | Required? | Role |
| --- | --- | --- |
| `AWS_REGION` | Recommended | Defaults to `us-east-1` if empty |
| `HAYSTACK_IMAGE` | Required for `deploy` / `configure-only` unless `image_ref` is set | Public GHCR or ECR tag. **No stock uvicorn.** |
| `IMAGE_HTTP_URL` | Optional | HTTPS or `s3://` CI `.tar.gz` for `docker load` |

### Run form

| Input | Use |
| --- | --- |
| `aws_environment` | Must be **`academy`** |
| `aws_access_key_id` / `aws_secret_access_key` / `aws_session_token` | Fresh Vocareum keys (override Environment secrets) |
| `image_ref` | One-off tag if `HAYSTACK_IMAGE` is empty |
| `image_http_url` | One-off tar if `IMAGE_HTTP_URL` is empty |

**Minimum `verify`:** Environment `academy` + three Vocareum keys + `AWS_REGION`.  
**Minimum `deploy` / `configure-only`:** that, plus `HAYSTACK_IMAGE` or `image_ref` (or a tar **and** a matching tag).

---

## 6. AWS (infra, not GitHub)

This CD does **not** create the ASG or start Neo4j. Before any `deploy`:

1. Infra `action=apply` created `asg-haystack` (internal ALB `:8000`), Haystack RDS, Bolt NLB, `asg-neo4j`.
2. Infra `sync-secrets` filled **`heavy-rental/haystack`**.
3. Guests are InService and SSM Online (Start Lab if the session ended). Desired=0 → infra, not this CD.

The guest (`LabRole`) reads `heavy-rental/haystack`. `LLM_API_KEY` is never on the Run form or in the image.

---

## 7. Runtime env names (image can be right; keys may not)

App `Settings` (`app/config.py`) uses different names and **CI-safe defaults**. `DATABASE_URL` from SM wins for Postgres and is rewritten `postgresql://` → `postgresql+psycopg://`.

**Owner:** infra `sync-secrets` writes the names the app reads (same idea as REST aliases). Haystack CD still **fills missing keys only** after SM → `.env` so an old secret still works. It does not overwrite a value already in the secret.

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
| `INDEXING_DOCUMENT_STORE` | not written → app default **`memory`** | **not** flipped (pgvector is optional) |
| `NEED_DECOMPOSER` | not written → **`stub`** | Haystack Environment `NEED_DECOMPOSER` overlays if set |
| `LLM_API_KEY` | optional on infra SM | Haystack Environment secret overlays if set; never invented |
| `LLM_BASE_URL` / `LLM_MODEL` / `LLM_TIMEOUT_SECONDS` / `LLM_TEMPERATURE` | not written → app defaults | set in SM or `docker -e` |
| `INDEXING_EMBEDDER` / `INDEXING_EMBEDDING_DIM` / `INDEXING_SPLIT_*` / `INDEXING_OPENAI_EMBEDDING_MODEL` / `INDEXING_CHUNK_TTL_SECONDS` | not written → mock / 384 / 200 / 20 / `text-embedding-3-small` / 0 | set in SM or `docker -e` |
| `IDEMPOTENCY_TTL_SECONDS` / `INDEXING_VIA_AGENT_GATE` | not written → 86400 / `false` | set in SM or `docker -e` |
| `PRICING_SCHEMA` | not written → `primary_snapshot` | set in SM (`public` for live Spring tables) |
| `NEO4J_POPULATE_URL` | **`http://neo4j-populate:8089/v1/populate`** (compose worker on `asg-haystack`) | **not** overlaid; infra SM owns it |
| `NEO4J_POPULATE_TIMEOUT_SECONDS` | not written → `2` | Haystack Environment overlay if set |
| `RECOMMEND_VIA_AGENT_GRAPH` / `KG_ARTIFACT_DIR` / `KG_APPLY_TRANSFORMS` | not written → `false` / `artifacts/kg` / `false` | set in SM or `docker -e` |
| `SOURCE_HOST` / `SOURCE_PORT` / `SOURCE_DATABASE` | written (SoR / REST RDS `heavy_rental`) | **not** invented by CD |
| `TARGET_HOST` / `TARGET_PORT` / `TARGET_DATABASE` | written (Haystack RDS — same host as `POSTGRES_*`) | **not** invented by CD |

`postgres-haystack-sync` is supposed to copy SoR → Haystack RDS using those `SOURCE_*` / `TARGET_*` keys from `heavy-rental/haystack`. Infra `sync-secrets` is the owner. Haystack CD maps the secret to `.env` and must **not** invent hosts, invent a third database, or copy `heavy-rental/rest`. There is no separate `SOURCE_USER` / `SOURCE_PASSWORD` today — if the worker needs credentials it reuses `POSTGRES_USERNAME` / `POSTGRES_PASSWORD` (same Academy master password on both RDS instances).

Re-run infra `configure-only` (or `apply`) so SM is rewritten. Infra first-compose then sees `sql` / `bolt` without waiting for app CD.

Haystack RDS database name is **`haystack`**, not the app example `heavy_rental`. `DATABASE_URL` from SM is the source of truth for uvicorn. `SOURCE_DATABASE` is **`heavy_rental`**.

`INDEXING_DOCUMENT_STORE=pgvector` still needs `CREATE EXTENSION vector` on Haystack RDS (infra `rds_logical`) and a matching `INDEXING_EMBEDDING_DIM`. Set `INDEXING_DOCUMENT_STORE` (and dim) on the **Haystack** Environment `academy`, then run Haystack CD `configure-only` — do not put that in infra `sync-secrets`.

Profile knobs (`NEED_DECOMPOSER`, `LLM_*`, `INDEXING_*`, `PRICING_SCHEMA`, `KG_*`, …) are Haystack project Environment variables/secrets. Infra still owns hosts, Bolt NLB `NEO4J_URI`, and RDS passwords.

---

## 8. Compose sidecars vs the live app

CD / estate compose (no `neo4j` service):

| Service | Limits | Command |
| --- | --- | --- |
| `haystack` (uvicorn) | `768m` / `1.0` | image `CMD` (`uv run uvicorn … :8000`) |
| `postgres-haystack-sync` | `256m` / `0.25` | `uv run python -m postgres_haystack_sync` |
| `neo4j-populate` | `256m` / `0.25` | `uv run python -m neo4j_populate` |

On app `develop` there is **no** `postgres_haystack_sync` or `neo4j_populate` package (only `scripts/export_eval_test_data.py`). The generated Dockerfile copies `app/` only.

Those two containers **crash-loop** (`restart: on-failure`). `compose up -d` still succeeds. CD `verify` only waits on uvicorn `:8000`. SoR → Haystack RDS sync and KG-2 populate do **not** run.

The app’s populate hook is HTTP, not `python -m`:

- `NEO4J_POPULATE_URL` default `http://neo4j-populate:8089/v1/populate`
- `trigger_neo4j_populate` POSTs that URL
- Compose does not publish `:8089`

**App-repo work** (not this CD YAML): ship the two modules **or** change the populate contract to an HTTP server on `:8089`. Do not start a `neo4j` container on `asg-haystack`.

---

## 9. What a forced `action=deploy` would do

1. **Today, on the app repo:** fail immediately — no CD workflow, no `HAYSTACK_IMAGE`, no GHCR tag.
2. **After copy + public image:** uvicorn can start; `/docs` / `/health` can pass; aliases + `FLEET_BACKEND=sql` + `NEO4J_BACKEND=bolt` are on `.env`; sync + populate crash-loop; Bolt still needs the `neo4j` extra in the image; Call 2 reads Haystack RDS `assets` only if that table exists.

That is still not the full QUICKSTART Profile B path until the sidecars (or HTTP populate) exist.

---

## 10. First CD run

1. Instructure → Start Lab → AWS Details.
2. Actions → **Haystack CD (Academy)** → Environment `academy` → paste the three keys (or use Environment fallback).
3. `action=verify` — assert-lab + discover + SSM `GET :8000/docs` or `/health` (SoR/Bolt down does not fail this job by itself if uvicorn answers).
4. `action=deploy` with a **new** public GHCR or ECR tag (or tar URL + matching tag).
5. `action=configure-only` refreshes `.env` from `heavy-rental/haystack` and applies the aliases/live flags (still needs `HAYSTACK_IMAGE` or `image_ref` — no stock uvicorn).

---

## 11. Do not

- Use CI Environments `integration` / `production` as CD
- Expect GHCR from HR-155 or a `develop`→`master` PR alone
- Put Vocareum keys or `LLM_API_KEY` in the image or on the Run form
- Type instance IDs on the Run form
- Run `terraform apply` from this workflow
- Start a `neo4j` container on `asg-haystack`
- Set `NEO4J_URI=bolt://neo4j:7687` or a guest private IP
- Treat a green `verify` as proof that sync or populate ran
