# Implementation plan: REST API app CD (Academy)

**Contract:** [`REST-API-CD-FEASIBILITY.md`](REST-API-CD-FEASIBILITY.md), [`../ANSIBLE-PROCESS.md`](../ANSIBLE-PROCESS.md), AWS study §6.0c / §6.4a.  
**Live estate:** `heavy-rental-project-instructure-and-cloud-deploy` (`HR-162` configure). First compose of Tomcat on `asg-rest` already exists there.  
**This plan is the delivery split.** Live YAML is in `heavy-rental-rest-api/deploy-pipeline/`.

**Status:** Infra branches 1–3 exist. Portal CD branch 2 exists. REST CD **branch 1** (discover) and **branch 2** (compose) are in `deploy-pipeline/` (`add-rest-cd-academy-deploy`). Paid REST CD is later.

Conflict order if that repo uses OpenSpec: OpenSpec → OpenSPDD → ADR → YAML / Ansible.

---

## 1. Goal

Manually deploy a **CI-built Tomcat + WAR image** onto the **existing** `asg-rest` (desired=2, both InService) without Terraform and without rebuilding the WAR.

- Image: **`tomcat:10.1-jdk21-temurin`** + `ROOT.war`, Java **21**, GHCR `ghcr.io/<owner>/heavy-rental-rest-api`.
- Internal REST ALB `:8080` only. Never on the public portal listener.
- Guest reads `heavy-rental/rest` (Postgres / JDBC, `HAYSTACK_BASE_URL`, Stripe secret + webhook + publishable). Password is **not** in the image.
- No Bolt on REST. No `docker build` / Maven on the guest.

**Non-goals:** `terraform apply`; `mvn package` / `docker build`; portal / Haystack / Neo4j deploy; `stop` / `destroy` (infra CD); paid / OIDC; instance IDs on the Run form; CI Environments `integration` / `production` as CD auth.

---

## 2. Where it lives

| Piece | Location |
| --- | --- |
| Workflow | Packaged in `heavy-rental-rest-api/deploy-pipeline/` (caller + reusable). Copy into the Spring repo `.github/` like Release CI. |
| Ansible | Copied into `deploy-pipeline/ansible/` from infra `guest_base` + `rest` (`--limit rest`). Do not invent a second compose contract |
| Inventory | Same idea as infra `inventory/aws_ssm.py`, **rest group only** (`asg-rest`) |
| Auth | Environment **`academy`** (same secret **names** as infra). Vocareum keys: `$GITHUB_EVENT_PATH` + `::add-mask::`. Never `${{ inputs.aws_* }}` in `env:` |

Academy only in this minimum. Paid = later workflow, OIDC, **no** key fields.

---

## 3. Prerequisite (fail closed)

Before any `deploy`:

1. Infra `action=apply` has created `asg-rest` (and the **internal** REST ALB).
2. Infra `sync-secrets` has filled `heavy-rental/rest` (`POSTGRES_*` / `SPRING_DATASOURCE_*`, `HAYSTACK_BASE_URL`, `STRIPE_API_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PUBLISHABLE_KEY`).
3. Guests are **InService** and **SSM Online** (Start Lab if the session ended). If desired=0, run infra (scale / `configure-only`) first — this CD must not change ASG desired.

Discover with AWS API (`asg-rest`). Do not paste instance IDs.

---

## 4. Optimal minimum branches: **2**

```
develop
  ├── feat/cd-rest-academy-skeleton    # 1
  └── feat/cd-rest-academy-deploy      # 2  (after 1)
```

| Count | Problem |
| --- | --- |
| **1** | Auth + discover + image + compose in one PR hides a dead Vocareum session behind Ansible. |
| **2** | Prove `assert-lab` + discover green **before** pulling images. |

---

## 5. Branch 1 — `feat/cd-rest-academy-skeleton`

**Purpose:** Actions can authenticate and **see** `asg-rest`. No compose.

### Tasks

1. OpenSpec (if used): rest-cd-academy-auth, rest-cd-discover, rest-cd-scope (no terraform, no portal / haystack / neo4j group).
2. Copy example YAML → `rest-api-cd-academy.yml` (caller + reusable in `deploy-pipeline/`).
3. Inputs: `action` (`deploy` / `configure-only` / `verify`), `aws_environment` (must be `academy`), optional `image_ref` / `image_http_url`, three Vocareum keys (optional if Environment set).
4. Resolve keys like infra / portal CD (`$GITHUB_EVENT_PATH`, mask, Environment fallback). Refuse Environment ≠ `academy`.
5. **`assert-lab`:** `sts get-caller-identity`. Output lab state bucket name for later SSM (`heavy-rental-tfstate-${ACCOUNT}-academy`).
6. **`discover-targets`:** InService IDs on `asg-rest`; keep SSM Online. Fail if none or desired=0. `describe-secret heavy-rental/rest` (do not echo SecretString). Fail if the shell is missing. Do **not** print instance IPs or the internal REST ALB URL.
7. `deploy` / `configure-only` ansible job **failed closed** on branch 1 (`exit 1` — “branch 2”). **Superseded** by §6.
8. **`verify`** was discover-only on branch 1. **Superseded** by §6 SSM `GET :8080`.

### Done when (branch 1)

Start Lab → Run workflow → `assert-lab` + `discover-targets` green. No image pull. No terraform. **Shipped** in `deploy-pipeline/` (`rest-api-cd-academy.yml`).

---

## 6. Branch 2 — `feat/cd-rest-academy-deploy`

**Purpose:** New CI image (or refresh `.env`) on both REST guests.

### Job graph

| `action` | Jobs |
| --- | --- |
| `deploy` | assert-lab → discover → resolve-image → ansible-rest → verify |
| `configure-only` | assert-lab → discover → ansible-rest (current/same image, refresh secret) → verify |
| `verify` | assert-lab → discover → health only |

### Tasks

1. **`resolve-image`** (pipeline layer, not invented in the playbook):
   - Non-empty `image_http_url` / `vars.IMAGE_HTTP_URL` → extra-var for `docker load`. Compose still needs a tag that matches the loaded image (`image_ref` or `REST_IMAGE`).
   - Else `image_ref` or Environment **`REST_IMAGE`** as a registry tag.
   - **`action=deploy` with both empty → fail.** There is no stock Tomcat fallback (unlike portal `nginx`).
   - Public **GHCR:** pull, no login.
   - **ECR** (`*.dkr.ecr.*`): guest `aws ecr get-login-password` (`LabRole`).
   - Private GHCR: **fail** (copy to ECR or use a tar). Do not put a PAT on the guest.
   - Prefer a **new tag** (`compose up` does not `--pull always`).
2. Runner: Ansible **14.3.1**, `amazon.aws` **>=11.3.0,<12**, `boto3/botocore>=1.35.0`, Session Manager plugin. Connection **`amazon.aws.aws_ssm`**. S3 bucket for the plugin = lab state bucket (same as infra / portal CD).
3. **`ansible-playbook … --limit rest`:** `guest_base` + `rest` only. §6.4a `1g` / `1.0`. Fail if `rest_image` empty. No Bolt. No public listener. Stripe `sk_` stays in `heavy-rental/rest` on the guest `.env` — **not** in the image and **not** on `asg-portal`.
4. **`configure-only`:** skip resolve-image. Use Environment `REST_IMAGE` or Run `image_ref`. Still **fail** if both empty (do not invent a Tomcat tag).
5. **`verify`:** SSM `GET http://127.0.0.1:8080/actuator/health` or `GET /` (200–302, and 401/403 if the app is up but locked). Do **not** fail solely because Haystack (`HAYSTACK_BASE_URL`) is down. Do **not** print instance IPs or `REST_BASE_URL`. Internal ALB DNS is optional and not required.

### Done when (branch 2)

`action=deploy` with a public GHCR or ECR tag updates **both** `asg-rest` guests. Internal ALB `:8080` serves the new WAR. `verify` is green if Tomcat answers. **Shipped** in `deploy-pipeline/` (`rest-api-cd-academy.yml` + `ansible/`).

---

## 7. After these two branches (not in the minimum)

| Next | Why it waited |
| --- | --- |
| Paid REST CD (`rest-api-cd-paid.yml`) | OIDC; no Vocareum keys |
| Haystack app CD | Same pattern, `asg-haystack` |
| `--pull always` / digest pins | Optional hardening |

Infra **`apply`** still first-composes REST. Infra **`configure-only`** does **not** compose REST. After that, use this app CD.

---

## 8. Forbidden in every branch

- `terraform apply` / creating `asg-rest`
- `mvn package`, `docker build` on the runner or guest
- Deploying portal, Haystack, or Neo4j (no those Ansible groups)
- Putting `STRIPE_API_KEY` in the image or on the portal
- Using CI Environments `integration` / `production` (`REST_API_DB_*` / `REST_API_CLOUD_DB_*`) as CD
- Instance ID / SSH host / private IP on `workflow_dispatch`
- Vocareum keys in Secrets Manager or on the guest
- Key fields on **paid** workflows
- `stop` / `destroy`
- Opening `:8080` or `:5432` to the public internet

---

## 9. Pointers

- Study: [`REST-API-CD-FEASIBILITY.md`](REST-API-CD-FEASIBILITY.md) §4–§8
- Example: [`rest-api-cd-pipeline.example.yml`](rest-api-cd-pipeline.example.yml)
- Sibling: [`../web-portal-CD-feasibility/IMPLEMENTATION-PLAN.md`](../web-portal-CD-feasibility/IMPLEMENTATION-PLAN.md)
- Infra operate: estate `docs/BOOTSTRAP.md` / `docs/ARCHITECTURE.md`
- Ansible contract: [`../ANSIBLE-PROCESS.md`](../ANSIBLE-PROCESS.md)
- CI: [`../../heavy-rental-rest-api/release-pipeline/`](../../heavy-rental-rest-api/release-pipeline/)
- Specs (OpenSpec / OpenSPDD / ADR): [`../../heavy-rental-rest-api/specification/`](../../heavy-rental-rest-api/specification/)
