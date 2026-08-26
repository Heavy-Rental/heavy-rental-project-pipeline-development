# Haystack app CD family (Academy + paid)

**Application:** https://github.com/Heavy-Rental/haystack-fast-api  
**Authoring tree:** `haystack-fast-api-pipeline/deploy-pipeline/`  
**Consumes:** public GHCR/ECR tag or Release image tar from the CI family ([`haystack-ci.md`](haystack-ci.md))

This family discovers `asg-haystack` and can re-run Haystack compose. It does **not** run Terraform, create the ASG, or start Neo4j. Infra `apply` + `sync-secrets` must already have created the guests and `heavy-rental/haystack`.

App-repo readiness and env/sidecar gaps: [`../../docs/PREPARE-HAYSTACK-REPO.md`](../../docs/PREPARE-HAYSTACK-REPO.md). Everyday operate: [`../../docs/BOOTSTRAP.md`](../../docs/BOOTSTRAP.md).

## Actions

```
Two callers (same reusable jobs):
  haystack-cd-academy-caller.yml   Environment academy + Vocareum keys
  haystack-cd-paid-caller.yml      Environment AWS_ACTUAL + OIDC, no Vocareum keys
      │
      ▼
 assert               academy: refuse non-academy, resolve keys (masked), sts
                      paid: refuse non-AWS_ACTUAL, OIDC, no AWS_ACCESS_KEY_ID
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
| `configure-only` | Yes (refresh guest `.env` + overlay; does **not** rebuild the image) | `HAYSTACK_IMAGE` or `image_ref` (or tar **and** matching tag). **No stock uvicorn.** |
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
| `NEED_DECOMPOSER`, `LLM_*`, `INDEXING_*`, `PRICING_SCHEMA`, `KG_*`, `APP_ENV`, … | Product Profile A/B | Image `/app/.env` from `.env.prod`; Haystack Environment `academy` overlay (ADR 0009) |

Haystack CD SHALL map SM → `.env` and MAY add FastAPI aliases (`POSTGRES_HOSTNAME`, …). It SHALL NOT invent `SOURCE_*` / `TARGET_*`, SHALL NOT copy `heavy-rental/rest`, and SHALL NOT bake RDS DNS into the image or the workflow YAML. No `SOURCE_USER` / `SOURCE_PASSWORD` in SM today — same Academy master password on both instances.

## Job graph

```
assert (academy Vocareum | paid OIDC)
      │
      ▼
 discover-targets
      │
      ├── resolve-image     (deploy / configure-only)
      ├── ansible-haystack  guest_base + haystack only; --limit haystack
      └── verify            SSM GET :8000/docs or /health (200–302)
```

Paid Ansible SSM uses `heavy-rental-ssm-<account>-actual` (not the tfstate bucket). Academy keeps the tfstate bucket for SSM transfer.

## Environment `academy`

| Kind | Name | Role |
| --- | --- | --- |
| Secret (optional fallback) | `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_SESSION_TOKEN` | Runner only, if the Run form is empty |
| Variable | `AWS_REGION` | Defaults to `us-east-1` |
| Variable | `HAYSTACK_IMAGE` | Public GHCR or ECR tag |
| Variable | `IMAGE_HTTP_URL` | Optional HTTPS or `s3://` CI tar |
| Secret (optional) | `LLM_API_KEY` | Overlay onto `.env`; never on the Run form |
| Variables (optional) | `APP_NAME`, `APP_ENV`, `LOG_LEVEL`, `NEED_DECOMPOSER`, `LLM_*`, `INDEXING_*` (incl. `INDEXING_ST_MODEL`), `PRICING_SCHEMA`, `KG_*`, `PROJECT_AGENT_*`, `RECOMMEND_FANOUT_CAP`, … | Product Profile; empty leaves SM / image `/app/.env` / app default. **Not** `NEO4J_URI` / `NEO4J_POPULATE_URL` |

Run form (academy): `aws_environment=academy`, Vocareum keys, optional `image_ref` / `image_http_url`.

The academy **runner** uses Vocareum keys. The academy **EC2** uses `LabRole`. Do not point this workflow at CI Environments `integration` or `production`.

## Environment `AWS_ACTUAL`

| Kind | Name | Role |
| --- | --- | --- |
| Variable or secret | `AWS_ROLE_TO_ASSUME` | GitHub OIDC. Required on paid |
| Variable | `AWS_REGION` | Defaults to `us-east-1` |
| Variable | `HAYSTACK_IMAGE` | Public GHCR or ECR tag (**this** Environment’s copy) |
| Variable | `IMAGE_HTTP_URL` | Optional HTTPS or `s3://` CI tar |

Paid caller declares **no** Vocareum key inputs. It fails if Environment is not `AWS_ACTUAL`, if `AWS_ACCESS_KEY_ID` is set, or if `AWS_ROLE_TO_ASSUME` is empty. The **EC2** uses `hr-paid-haystack`. Same optional Profile overlay names as academy, on **this** Environment.

## Install into the application repo

Copy from `deploy-pipeline/`:

| Source | Destination in haystack-fast-api |
| --- | --- |
| `haystack-cd-academy-caller.yml` | `.github/workflows/` |
| `haystack-cd-paid-caller.yml` | `.github/workflows/` |
| `haystack-cd-academy.yml` | `.github/workflows/` |
| `resolve-aws-profile/action.yml` | `.github/actions/resolve-aws-profile/` |
| `ansible/` | **`deploy-pipeline/ansible/`** (keep this path) |

Do **not** copy `specification/`.

## Local validation (this repo)

```bash
actionlint haystack-fast-api-pipeline/deploy-pipeline/haystack-cd-academy.yml
actionlint haystack-fast-api-pipeline/deploy-pipeline/haystack-cd-academy-caller.yml
actionlint haystack-fast-api-pipeline/deploy-pipeline/haystack-cd-paid-caller.yml
```

## Pipeline boundaries

| Concern | In this CD family? |
| --- | --- |
| Discover `asg-haystack` and compose Haystack | Yes |
| Terraform / create ASG / start Neo4j | No — infra project |
| Ansible groups portal / rest / neo4j | No |
| Rebuild the image | No — consume Release artifacts |
| `stop` / `destroy` | No — infra CD |
| Paid / OIDC | Yes — `haystack-cd-paid-caller.yml` (ADR 0010) |

## Specs

- OpenSpec: [`../../openspec/changes/add-haystack-cd-academy-skeleton/`](../../openspec/changes/add-haystack-cd-academy-skeleton/), [`../../openspec/changes/add-haystack-cd-academy-deploy/`](../../openspec/changes/add-haystack-cd-academy-deploy/), [`../../openspec/changes/add-haystack-cd-paid-deploy/`](../../openspec/changes/add-haystack-cd-paid-deploy/)
- OpenSPDD: [`../../spdd/analysis/add-haystack-cd-academy-deploy.md`](../../spdd/analysis/add-haystack-cd-academy-deploy.md), [`../../spdd/analysis/add-haystack-cd-paid-deploy.md`](../../spdd/analysis/add-haystack-cd-paid-deploy.md)
- ADRs 0001–0004, 0009–0010: [`../../docs/adr/`](../../docs/adr/)
