# Implementation plan: Web portal app CD (Academy)

**Contract:** [`WEB-PORTAL-CD-FEASIBILITY.md`](WEB-PORTAL-CD-FEASIBILITY.md), [`../ANSIBLE-PROCESS.md`](../ANSIBLE-PROCESS.md), AWS study §6.0c / §6.4a / §6.6.  
**Live estate:** `heavy-rental-project-instructure-and-cloud-deploy` (`HR-162` configure). First compose and `/api` proxy already exist there.  
**This plan is the delivery split.** Live YAML is in `heavy-rental-web-portal-pipeline/deploy-pipeline/`.

**Status:** Infra branches 1–3 exist. Portal CD **branch 1** (discover) and **branch 2** (compose) are in `deploy-pipeline/` (`add-portal-cd-academy-deploy`). Paid portal CD is later.

Conflict order if that repo uses OpenSpec: OpenSpec → OpenSPDD → ADR → YAML / Ansible.

---

## 1. Goal

Manually deploy a **CI-built nginx + Vite `dist/` image** onto the **existing** `asg-portal` (desired=2, both InService) without Terraform and without rebuilding the SPA.

- Browser → public portal ALB `:80` → nginx + `dist/`.
- nginx `location /api/` → `REST_BASE_URL` from `heavy-rental/portal` (internal REST ALB).
- No Vite server in AWS. No `sk_` / `whsec_` on the portal.

**Non-goals:** `terraform apply`; `npm run build` / `docker build`; REST / Haystack / Neo4j deploy; `stop` / `destroy` (infra CD); paid / OIDC; instance IDs on the Run form.

---

## 2. Where it lives

| Piece | Location |
| --- | --- |
| Workflow | Packaged in `heavy-rental-web-portal-pipeline/deploy-pipeline/` (caller + reusable). Copy into the React repo `.github/` like Release CI. |
| Ansible | Copied into `deploy-pipeline/ansible/` from infra `guest_base` + `portal` (`--limit portal`). Do not invent a second compose contract |
| Inventory | Same idea as infra `inventory/aws_ssm.py`, **portal group only** (`asg-portal`) |
| Auth | Environment **`academy`** (same secret **names** as infra). Vocareum keys: `$GITHUB_EVENT_PATH` + `::add-mask::`. Never `${{ inputs.aws_* }}` in `env:` |

Academy only in this minimum. Paid = later workflow, OIDC, **no** key fields.

---

## 3. Prerequisite (fail closed)

Before any `deploy`:

1. Infra `action=apply` has created `asg-portal` (and the public ALB).
2. Infra `sync-secrets` has filled `heavy-rental/portal` (`REST_BASE_URL`, `STRIPE_PUBLISHABLE_KEY`, `VITE_STRIPE_PUBLISHABLE_KEY`).
3. Guests are **InService** and **SSM Online** (Start Lab if the session ended). If desired=0, run infra (scale / `configure-only`) first — this CD must not change ASG desired.

Discover with AWS API (`asg-portal`). Do not paste instance IDs.

---

## 4. Optimal minimum branches: **2**

```
develop
  ├── feat/cd-portal-academy-skeleton    # 1
  └── feat/cd-portal-academy-deploy      # 2  (after 1)
```

| Count | Problem |
| --- | --- |
| **1** | Auth + discover + image + compose in one PR hides a dead Vocareum session behind Ansible. |
| **2** | Prove `assert-lab` + discover green **before** pulling images. |

---

## 5. Branch 1 — `feat/cd-portal-academy-skeleton`

**Purpose:** Actions can authenticate and **see** `asg-portal`. No compose.

### Tasks

1. OpenSpec (if used): portal-cd-academy-auth, portal-cd-discover, portal-cd-scope (no terraform, no REST group).
2. Copy example YAML → `web-portal-cd-academy.yml`.
3. Inputs: `action` (`deploy` / `configure-only` / `verify`), `aws_environment` (must be `academy`), optional `image_ref` / `image_http_url`, three Vocareum keys (optional if Environment set).
4. Resolve keys like infra (`$GITHUB_EVENT_PATH`, mask, Environment fallback). Refuse Environment ≠ `academy`.
5. **`assert-lab`:** `sts get-caller-identity`.
6. **`discover-targets`:** InService IDs on `asg-portal`; keep SSM Online. Fail if none. Optional: public portal ALB DNS in the job summary (not instance IPs). `describe-secret heavy-rental/portal` (do not echo SecretString). Fail if the shell is missing.
7. `deploy` / `configure-only` ansible job **failed closed** on branch 1 (`exit 1` — “branch 2”). **Superseded** by §6.
8. **`verify`** was discover-only on branch 1. **Superseded** by §6 SSM `GET /`.

### Done when (branch 1)

Start Lab → Run workflow → `assert-lab` + `discover-targets` green. No image pull. No terraform. **Shipped.**

---

## 6. Branch 2 — `feat/cd-portal-academy-deploy`

**Purpose:** New CI image (or refresh `.env` / `/api`) on both portal guests.

### Job graph

| `action` | Jobs |
| --- | --- |
| `deploy` | assert-lab → discover → resolve-image → ansible-portal → verify |
| `configure-only` | assert-lab → discover → ansible-portal (current/same image, refresh secret + `/api`) → verify |
| `verify` | assert-lab → discover → health only |

### Tasks

1. **`resolve-image`** (pipeline layer, not invented in the playbook):
   - Non-empty `image_http_url` / `vars.IMAGE_HTTP_URL` → extra-var for `docker load`.
   - Else `image_ref` or Environment **`PORTAL_IMAGE`** as a registry tag.
   - Public **GHCR:** pull, no login.
   - **ECR** (`*.dkr.ecr.*`): guest `aws ecr get-login-password` (`LabRole`).
   - Private GHCR: **fail** (copy to ECR or use a tar). Do not put a PAT on the guest.
   - Prefer a **new tag** (`compose up` does not `--pull always`).
2. Runner: Ansible **14.3.1**, `amazon.aws` **>=11.3.0,<12**, `boto3/botocore>=1.35.0`, Session Manager plugin. Connection **`amazon.aws.aws_ssm`**. S3 bucket for the plugin = lab state bucket (same as infra).
3. **`ansible-playbook … --limit portal`:** `guest_base` + `portal` only. `/api` → `REST_BASE_URL`. §6.4a `256m` / `0.5`. Fail if `REST_BASE_URL` empty. Refuse `STRIPE_API_KEY` / `STRIPE_WEBHOOK_SECRET` / PEM on the portal `.env`.
4. **`verify`:** SSM `GET /` on `:80` (200–302). Do **not** fail solely because `/api` (REST) is down. Summary may print **public** portal ALB DNS only.

### Done when (branch 2)

`action=deploy` with a public GHCR or ECR tag updates **both** `asg-portal` guests. Public ALB `:80` serves the new SPA. `/api` still proxies to the internal REST ALB. `verify` is green if nginx answers. **Shipped** in `deploy-pipeline/` (`web-portal-cd-academy.yml` + `ansible/`).

---

## 7. After these two branches (not in the minimum)

| Next | Why it waited |
| --- | --- |
| Paid portal CD (`web-portal-cd-paid.yml`) | OIDC; no Vocareum keys |
| REST / Haystack app CD | Same pattern, different group |
| `--pull always` / digest pins | Optional hardening |

Infra **`apply`** still first-composes the portal. Infra **`configure-only`** does **not** compose the portal. After that, use this app CD.

---

## 8. Forbidden in every branch

- `terraform apply` / creating `asg-portal`
- `npm run build`, `tsc`, `docker build`, Vite in AWS
- Baking `REST_BASE_URL` into a public GHCR / `VITE_*` bundle
- `STRIPE_API_KEY` / `STRIPE_WEBHOOK_SECRET` on the portal secret, image, or `.env`
- Instance ID / SSH host / private IP on `workflow_dispatch`
- Vocareum keys in Secrets Manager or on the guest
- Key fields on **paid** workflows
- Ansible groups `rest`, `haystack`, `neo4j`
- `stop` / `destroy`

---

## 9. Pointers

- Study: [`WEB-PORTAL-CD-FEASIBILITY.md`](WEB-PORTAL-CD-FEASIBILITY.md) §5–§8
- Example: [`web-portal-cd-pipeline.example.yml`](web-portal-cd-pipeline.example.yml)
- Infra operate: estate `docs/BOOTSTRAP.md` / `docs/ARCHITECTURE.md`
- Ansible contract: [`../ANSIBLE-PROCESS.md`](../ANSIBLE-PROCESS.md)
- Specs (OpenSpec / OpenSPDD / ADR): [`../../heavy-rental-web-portal-pipeline/specification/`](../../heavy-rental-web-portal-pipeline/specification/)
