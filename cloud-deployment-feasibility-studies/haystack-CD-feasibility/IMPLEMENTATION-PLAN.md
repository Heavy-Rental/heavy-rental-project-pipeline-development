# Implementation plan: Haystack FastAPI app CD (Academy)

## As-built (read this first)

Academy branches 1–2 **and** paid Haystack CD are **delivered** (`add-haystack-cd-academy-deploy`, `add-haystack-cd-paid-deploy`, ADR 0010, Environment `AWS_ACTUAL`). GHCR is `haystack_recommender`. Release is `workflow_dispatch` only. Living specs: [`../../haystack-fast-api-pipeline/specification/`](../../haystack-fast-api-pipeline/specification/). Body below is the original Academy two-branch split.

**Contract:** [`HAYSTACK-CD-FEASIBILITY.md`](HAYSTACK-CD-FEASIBILITY.md), [`../ANSIBLE-PROCESS.md`](../ANSIBLE-PROCESS.md) §4.3, AWS study §6.0c / §6.4a.  
**Live estate:** `heavy-rental-project-instructure-and-cloud-deploy`. Infra `apply` does **not** compose Haystack. First compose is infra `deploy-projects` (`site.yml`) or this app CD (uvicorn + `postgres:17` `sync-from-primary.sh` + `python:3.12-slim` `populate-neo4j-from-haystack.sh` wrapping `populate_neo4j.py`, **no** Neo4j container; Haystack ADR 0011).  
**This plan is the delivery split.** Live YAML is in `haystack-fast-api-pipeline/deploy-pipeline/`.

**Status:** Infra branches 1–3 exist. Haystack CD **branch 1** (discover), **branch 2** (compose), and **paid caller** are in `deploy-pipeline/`.

Conflict order if that repo uses OpenSpec: OpenSpec → OpenSPDD → ADR → YAML / Ansible.

---

## 1. Goal

Manually deploy a **CI-built uvicorn image** onto the **existing** `asg-haystack` (desired=2, both InService) without Terraform and without rebuilding the app.

- Image: **`python:3.12-slim-bookworm`** + uv + uvicorn `app.main:app` on **`:8000`**, GHCR `ghcr.io/<owner>/haystack_recommender`.
- Internal Haystack ALB `:8000` only. Never on the public portal listener.
- Guest reads `heavy-rental/haystack` (Haystack RDS `POSTGRES_*` including app aliases `POSTGRES_HOSTNAME` / `POSTGRES_DB` / `POSTGRES_USER`, `DATABASE_URL`, `FLEET_BACKEND=sql`, `NEO4J_BACKEND=bolt`, `NEO4J_URI` = Bolt **NLB** — not localhost, not a guest IP — user/password, optional `LLM_API_KEY`). Password is **not** in the image.
- Compose **uvicorn + postgres-haystack-sync + neo4j-populate**. **Must not** start a `neo4j` container.
- No `uv build` / `docker build` on the guest.

**Non-goals:** `terraform apply`; Ruff/pytest/`uv build`/`docker build`; portal / REST / `asg-neo4j` deploy; starting Neo4j on this host; `stop` / `destroy` (infra CD); paid / OIDC; instance IDs on the Run form; putting `LLM_API_KEY` in CI or in the image.

---

## 2. Where it lives

| Piece | Location |
| --- | --- |
| Workflow | Packaged in `haystack-fast-api-pipeline/deploy-pipeline/` (caller + reusable). Copy into the Haystack app repo `.github/` like Release CI. |
| Ansible | **Reuse** infra `ansible/roles/guest_base` + `roles/haystack` (`--limit haystack`). Copy — do not invent a second compose contract |
| Inventory | Same idea as infra `inventory/aws_ssm.py`, **haystack group only** (`asg-haystack`) |
| Auth | Environment **`academy`** (same secret **names** as infra). Vocareum keys: `$GITHUB_EVENT_PATH` + `::add-mask::`. Never `${{ inputs.aws_* }}` in `env:` |

Academy only in this **minimum**. Paid caller is **delivered** (`haystack-cd-paid-caller.yml`, OIDC, **no** key fields).

---

## 3. Prerequisite (fail closed)

Before any `deploy`:

1. Infra `action=apply` has created `asg-haystack`, the **internal** Haystack ALB, the **Bolt NLB**, Haystack RDS, and `asg-neo4j` (graph is **not** on this CD).
2. Infra `sync-secrets` has filled `heavy-rental/haystack` (Haystack RDS Postgres fields, `NEO4J_URI` / user / password, optional `LLM_API_KEY`).
3. Guests are **InService** and **SSM Online** (Start Lab if the session ended). If desired=0, run infra (scale / `configure-only`) first — this CD must not change ASG desired.

Discover with AWS API (`asg-haystack`). Do not paste instance IDs.

---

## 4. Optimal minimum branches: **2**

```
develop
  ├── feat/cd-haystack-academy-skeleton    # 1
  └── feat/cd-haystack-academy-deploy      # 2  (after 1)
```

| Count | Problem |
| --- | --- |
| **1** | Auth + discover + image + compose in one PR hides a dead Vocareum session behind Ansible. |
| **2** | Prove `assert-lab` + discover green **before** pulling images. |

---

## 5. Branch 1 — `feat/cd-haystack-academy-skeleton`

**Purpose:** Actions can authenticate and **see** `asg-haystack`. No compose.

### Tasks

1. OpenSpec (if used): haystack-cd-academy-auth, haystack-cd-discover, haystack-cd-scope (no terraform, no portal / rest / neo4j group).
2. Copy example YAML → `haystack-cd-academy.yml` (caller + reusable in `deploy-pipeline/`).
3. Inputs: `action` (`deploy` / `configure-only` / `verify`), `aws_environment` (must be `academy`), optional `image_ref` / `image_http_url`, three Vocareum keys (optional if Environment set).
4. Resolve keys like infra / portal / REST CD (`$GITHUB_EVENT_PATH`, mask, Environment fallback). Refuse Environment ≠ `academy`.
5. **`assert-lab`:** `sts get-caller-identity`. Output lab state bucket name for later SSM (`heavy-rental-tfstate-${ACCOUNT}-academy`).
6. **`discover-targets`:** InService IDs on `asg-haystack`; keep SSM Online. Fail if none or desired=0. `describe-secret heavy-rental/haystack` (do not echo SecretString). Fail if the shell is missing. Do **not** print instance IPs or the internal Haystack ALB URL.
7. `deploy` / `configure-only` ansible job **failed closed** on branch 1. **Superseded** by §6.
8. **`verify`** was discover-only on branch 1. **Superseded** by §6 SSM `GET :8000/health` **2xx**.

### Done when (branch 1)

Start Lab → Run workflow → `assert-lab` + `discover-targets` green. No image pull. No terraform. **Shipped** in `deploy-pipeline/` (`haystack-cd-academy.yml`).

---

## 6. Branch 2 — `feat/cd-haystack-academy-deploy`

**Purpose:** New CI image (or refresh `.env`) on both Haystack guests. Same sync + populate; still no Neo4j.

### Job graph

| `action` | Jobs |
| --- | --- |
| `deploy` | assert-lab → discover → resolve-image → ansible-haystack → verify |
| `configure-only` | assert-lab → discover → ansible-haystack (current/same image, refresh secret) → verify |
| `verify` | assert-lab → discover → health only |

### Tasks

1. **`resolve-image`** (pipeline layer, not invented in the playbook):
   - Non-empty `image_http_url` / `vars.IMAGE_HTTP_URL` → extra-var for `docker load`. Compose still needs a tag that matches the loaded image (`image_ref` or `HAYSTACK_IMAGE`).
   - Else `image_ref` or Environment **`HAYSTACK_IMAGE`** as a registry tag.
   - **`action=deploy` with both empty → fail.** There is no stock uvicorn fallback.
   - Public **GHCR:** pull, no login.
   - **ECR** (`*.dkr.ecr.*`): guest `aws ecr get-login-password` (`LabRole`).
   - Private GHCR: **fail** (copy to ECR or use a tar). Do not put a PAT on the guest.
   - Prefer a **new tag** (`compose up` does not `--pull always`).
2. Runner: Ansible **14.3.1**, `amazon.aws` **>=11.3.0,<12**, `boto3/botocore>=1.35.0`, Session Manager plugin. Connection **`amazon.aws.aws_ssm`**. S3 bucket for the plugin = lab state bucket (same as infra / portal / REST CD).
3. **`ansible-playbook … --limit haystack`:** `guest_base` + `haystack` only. §6.4a: uvicorn `768m` / `1.0`, sync `256m` / `0.25`, populate `256m` / `0.25`. Fail if `haystack_image` empty. **Must not** start a `neo4j` service. Sync `SOURCE_HOST` = SoR RDS; `TARGET_HOST` = Haystack RDS; Bolt = NLB `NEO4J_URI`. Optional `LLM_API_KEY` from SM only — never bake it into the image.
4. **`configure-only`:** skip resolve-image. Use Environment `HAYSTACK_IMAGE` or Run `image_ref`. Still **fail** if both empty.
5. **`verify`:** SSM `GET http://127.0.0.1:8000/health` must be **2xx** (same as ALB `tg-haystack` matcher `200-299`). Do **not** treat `/docs` as the ALB check. Do **not** fail solely because SoR RDS or Bolt is down if `/health` is 2xx. Do **not** print instance IPs or the internal ALB DNS.

### Done when (branch 2)

`action=deploy` with a public GHCR or ECR tag updates **both** `asg-haystack` guests. Internal ALB `:8000` serves the new uvicorn. Sync and populate still run. No Neo4j container. `verify` is green if uvicorn answers. **Shipped** in `deploy-pipeline/` (`haystack-cd-academy.yml` + `ansible/`).

---

## 7. After these two branches (not in the minimum)

| Next | Why it waited |
| --- | --- |
| Paid Haystack CD (`haystack-cd-paid-caller.yml`) | **Delivered** — OIDC; no Vocareum keys |
| `--pull always` / digest pins | Optional hardening |

Infra **`apply`** / **`configure-only`** do **not** compose Haystack. First-compose is infra **`deploy-projects`** or this app CD. After that, use this app CD for image rolls.

The live app repo is **not** ready to deploy (no Release/CD on `develop`, no GHCR image, sidecar modules missing). See [`PREPARE-HAYSTACK-REPO.md`](../../haystack-fast-api-pipeline/docs/PREPARE-HAYSTACK-REPO.md).

---

## 8. Forbidden in every branch

- `terraform apply` / creating `asg-haystack` or the Bolt NLB
- `uv build`, `docker build`, Ruff, pytest on this workflow
- Deploying portal, REST, or Neo4j (no those Ansible groups)
- Starting a `neo4j` container on `asg-haystack`
- `LLM_API_KEY` in CI, in the image, or on the Run form
- Instance ID / SSH host / private IP on `workflow_dispatch`
- Vocareum keys in Secrets Manager or on the guest
- Key fields on **paid** workflows
- `stop` / `destroy`
- Opening `:8000`, `:5432`, or `:7687` to the public internet
- `NEO4J_URI=bolt://neo4j:7687` or a guest private IP

---

## 9. Pointers

- Study: [`HAYSTACK-CD-FEASIBILITY.md`](HAYSTACK-CD-FEASIBILITY.md) §4–§8
- Example: [`haystack-cd-pipeline.example.yml`](haystack-cd-pipeline.example.yml)
- Siblings: [`../web-portal-CD-feasibility/IMPLEMENTATION-PLAN.md`](../web-portal-CD-feasibility/IMPLEMENTATION-PLAN.md), [`../rest-api-CD-feasibility/IMPLEMENTATION-PLAN.md`](../rest-api-CD-feasibility/IMPLEMENTATION-PLAN.md)
- Infra operate: estate `docs/BOOTSTRAP.md` / `docs/ARCHITECTURE.md`
- Ansible contract: [`../ANSIBLE-PROCESS.md`](../ANSIBLE-PROCESS.md) §4.3
- CI: [`../../haystack-fast-api-pipeline/release-pipeline/`](../../haystack-fast-api-pipeline/release-pipeline/)
- Specs (OpenSpec / OpenSPDD / ADR): [`../../haystack-fast-api-pipeline/specification/`](../../haystack-fast-api-pipeline/specification/)
- App-repo readiness: [`../../haystack-fast-api-pipeline/docs/PREPARE-HAYSTACK-REPO.md`](../../haystack-fast-api-pipeline/docs/PREPARE-HAYSTACK-REPO.md)
