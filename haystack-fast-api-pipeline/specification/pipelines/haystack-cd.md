# Haystack Academy CD family

**Application:** https://github.com/Heavy-Rental/haystack-fast-api  
**Authoring tree:** `haystack-fast-api-pipeline/deploy-pipeline/`  
**Consumes:** public GHCR/ECR tag or Release image tar from the CI family ([`haystack-ci.md`](haystack-ci.md))

This family discovers `asg-haystack` and can re-run Haystack compose. It does **not** run Terraform, create the ASG, or start Neo4j. Infra `apply` + `sync-secrets` must already have created the guests and `heavy-rental/haystack`.

App-repo readiness and env/sidecar gaps: [`../../docs/PREPARE-HAYSTACK-REPO.md`](../../docs/PREPARE-HAYSTACK-REPO.md). Everyday operate: [`../../docs/BOOTSTRAP.md`](../../docs/BOOTSTRAP.md).

## Actions

```
workflow_dispatch (Environment academy + Vocareum keys)
      │
      ▼
 assert-lab          refuse non-academy; resolve keys (masked); sts
      │
      ▼
 discover-targets    SSM inventory asg-haystack (InService + Online)
      │
      ├── action=verify           skip compose; SSM GET :8000/docs or /health
      ├── action=configure-only   refresh .env from SM + aliases + Profile overlay; needs image
      └── action=deploy           resolve-image → ansible haystack → verify
```

| Action | Compose? | Image required? |
| --- | --- | --- |
| `verify` | No | No |
| `configure-only` | Yes (refresh `.env`) | `HAYSTACK_IMAGE` or `image_ref` (or tar **and** matching tag). **No stock uvicorn.** |
| `deploy` | Yes | Same as configure-only. Prefer a **new** tag. |

`verify` waits on uvicorn `:8000` only. Sidecar crash-loops (`postgres-haystack-sync`, `neo4j-populate`) do not fail the job.

## Sync env (SoR → Haystack RDS)

`postgres-haystack-sync` shares the uvicorn image and `env_file: .env`. Database endpoints are **externalized** in `heavy-rental/haystack` by infra `sync-secrets`, not by this CD family and not by CI.

| Key | Meaning | Who writes it |
| --- | --- | --- |
| `POSTGRES_*` / `DATABASE_URL` | Haystack RDS (uvicorn) | Infra `sync-secrets` |
| `SOURCE_HOST` / `SOURCE_PORT` / `SOURCE_DATABASE` | SoR / REST RDS (`heavy_rental`) | Infra `sync-secrets` |
| `TARGET_HOST` / `TARGET_PORT` / `TARGET_DATABASE` | Haystack RDS (same host as `POSTGRES_*`) | Infra `sync-secrets` |
| `NEO4J_URI` | Bolt NLB | Infra Terraform → `sync-secrets` |
| `NEO4J_POPULATE_URL` | Compose worker `http://neo4j-populate:8089/v1/populate` | Infra `sync-secrets` (not an ALB) |
| `FLEET_BACKEND` / `NEO4J_BACKEND` | `sql` / `bolt` | Infra SM; Haystack Environment may overlay |
| `NEED_DECOMPOSER`, `LLM_*`, `INDEXING_*`, `PRICING_SCHEMA`, `KG_*`, … | Product Profile A/B | Haystack Environment `academy` (ADR 0009) |

Haystack CD SHALL map SM → `.env` and MAY add FastAPI aliases (`POSTGRES_HOSTNAME`, …). It SHALL NOT invent `SOURCE_*` / `TARGET_*`, SHALL NOT copy `heavy-rental/rest`, and SHALL NOT bake RDS DNS into the image or the workflow YAML. No `SOURCE_USER` / `SOURCE_PASSWORD` in SM today — same Academy master password on both instances.

## Job graph

```
assert-lab
      │
      ▼
 discover-targets
      │
      ├── resolve-image     (deploy / configure-only)
      ├── ansible-haystack  guest_base + haystack only; --limit haystack
      └── verify            SSM GET :8000/docs or /health (200–302)
```

## Environment `academy`

| Kind | Name | Role |
| --- | --- | --- |
| Secret (optional fallback) | `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_SESSION_TOKEN` | Runner only, if the Run form is empty |
| Variable | `AWS_REGION` | Defaults to `us-east-1` |
| Variable | `HAYSTACK_IMAGE` | Public GHCR or ECR tag |
| Variable | `IMAGE_HTTP_URL` | Optional HTTPS or `s3://` CI tar |
| Secret (optional) | `LLM_API_KEY` | Overlay onto `.env`; never on the Run form |
| Variables (optional) | `NEED_DECOMPOSER`, `LLM_*`, `INDEXING_*`, `PRICING_SCHEMA`, `KG_*`, … | Product Profile; empty leaves SM/app default. **Not** `NEO4J_URI` / `NEO4J_POPULATE_URL` |

Run form: `aws_environment=academy`, Vocareum keys, optional `image_ref` / `image_http_url`.

The **runner** uses Vocareum keys. The **EC2** uses `LabRole`. Do not point this workflow at CI Environments `integration` or `production`.

## Install into the application repo

Copy from `deploy-pipeline/`:

| Source | Destination in haystack-fast-api |
| --- | --- |
| `haystack-cd-academy-caller.yml` | `.github/workflows/` |
| `haystack-cd-academy.yml` | `.github/workflows/` |
| `resolve-vocareum-aws/action.yml` | `.github/actions/resolve-vocareum-aws/` |
| `ansible/` | **`deploy-pipeline/ansible/`** (keep this path) |

Do **not** copy `specification/`.

## Local validation (this repo)

```bash
actionlint haystack-fast-api-pipeline/deploy-pipeline/haystack-cd-academy.yml
actionlint haystack-fast-api-pipeline/deploy-pipeline/haystack-cd-academy-caller.yml
```

## Pipeline boundaries

| Concern | In this CD family? |
| --- | --- |
| Discover `asg-haystack` and compose Haystack | Yes |
| Terraform / create ASG / start Neo4j | No — infra project |
| Ansible groups portal / rest / neo4j | No |
| Rebuild the image | No — consume Release artifacts |
| `stop` / `destroy` | No — infra CD |
| Paid / OIDC | No — later workflow |

## Specs

- OpenSpec: [`../../openspec/changes/add-haystack-cd-academy-skeleton/`](../../openspec/changes/add-haystack-cd-academy-skeleton/), [`../../openspec/changes/add-haystack-cd-academy-deploy/`](../../openspec/changes/add-haystack-cd-academy-deploy/)
- OpenSPDD: [`../../spdd/analysis/add-haystack-cd-academy-deploy.md`](../../spdd/analysis/add-haystack-cd-academy-deploy.md)
- ADRs 0001–0004, 0009: [`../../docs/adr/`](../../docs/adr/)
