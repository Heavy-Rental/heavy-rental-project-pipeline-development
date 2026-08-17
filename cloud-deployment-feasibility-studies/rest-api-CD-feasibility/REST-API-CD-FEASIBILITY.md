# Feasibility study: CD for heavy-rental-rest-api

**Status:** Study only. Example workflows are stubs. This file does not apply Terraform or deploy a live service.

**Destinations:** same two AWS accounts as [`../AWS-INFRASTRUCTURE-FEASIBILITY.md`](../AWS-INFRASTRUCTURE-FEASIBILITY.md) — **Academy** and **Paid**. Environments `academy` / `paid`. One run must never touch the other.

**Manually triggered after the estate is up.** It does **not** create the VPC, `asg-rest`, the internal REST ALB, or RDS. If `asg-rest` is missing, **fail** and run infra CD `action=apply` first. Branch **1** (discover only) lives in `heavy-rental-rest-api/deploy-pipeline/`. Until branch **2** (compose) exists, redeploy REST with infra **`configure-only`** and Environment **`REST_IMAGE`**.

**The hard problem** is discovering the **private** EC2 (no public IP; IDs change after Start Lab). Do not type instance IDs on the form.

---

## 1. Purpose and non-goals

### Purpose

**Re-run the guest compose playbook** on an **already created** `asg-rest` EC2 with the **Tomcat + WAR image** REST CI Release already built. Infra Terraform created the instance; infra Ansible did the first compose. This pipeline is a **later, manual** compose run (new image only). No new EC2.

The Academy **skeleton** (branch 1: `assert-lab` + discover, compose jobs fail-closed) is in [`../../heavy-rental-rest-api/deploy-pipeline/`](../../heavy-rental-rest-api/deploy-pipeline/). Compose still belongs to **infra** until REST CD branch 2. See [`IMPLEMENTATION-PLAN.md`](IMPLEMENTATION-PLAN.md).

### Non-goals

- Maven package, Semgrep, CodeQL, or `docker build` from source
- `terraform apply`
- Deploying portal, Haystack, or Neo4j
- Putting Stripe `sk_` on the portal or in the image
- Using REST CI Environments `integration` / `production` as CD auth

---

## 2. Three pipelines (do not merge)

| Pipeline | Tree | Role |
| --- | --- | --- |
| **REST CI** | `heavy-rental-rest-api/` | Fast Feedback → Integration → **Release** (WAR + **Docker tar** + GHCR off PR) |
| **Infra CD** | `aws-infra-*.example.yml` | VPC, four ASGs, ALBs, RDS, SM, first compose |
| **REST app CD (this study)** | Live skeleton: `heavy-rental-rest-api/deploy-pipeline/`. Examples in this folder stay stubs. | Manual deploy of **this** image onto existing `asg-rest`. Branch 1 = discover only. Branch 2 (not built) = compose. |

### 2.1 Sequence

```
Infra CD  action=apply
    Terraform     →  creates asg-rest (EC2 InService)
    sync-secrets  →  heavy-rental/rest
    Ansible       →  first compose (Tomcat, §6.4a 1g / 1.0 cpu)

Later, new CI image:
REST app CD  (workflow_dispatch only)
    discover  →  asg-rest InService + SSM Online
    compose   →  same guest playbook, rest group only
                 docker load/pull CI image; compose up :8080
```

---

## 3. What CI already produces

From `heavy-rental-rest-api/release-pipeline/release-pipeline.yml`:

| Artifact | When | CD use |
| --- | --- | --- |
| Image tar (`tomcat:10.1-jdk21-temurin` + `ROOT.war`, Java **21**) | Always on Packaging | Academy: `docker load` or ECR in-region |
| GHCR `ghcr.io/<owner>/heavy-rental-rest-api:<version>` and `:latest` | Non-PR / published Release | Paid (Academy if pull works). **Not** pushed on develop→master PR |
| Versioned + stable WAR | Always | Optional; image is enough |

Image contract: **`tomcat:10.1-jdk21-temurin`** serving `ROOT.war` on **`:8080`**. Java **21**. Build does **not** start Postgres or Haystack.

Port **8080**. Health `GET /actuator/health` or `/`. Password is **not** in the artifact; CD uses Secrets Manager.

CI Environments: **`integration`** (`REST_API_DB_*`) and **`production`** (`REST_API_CLOUD_DB_*`). Those names are **not** CD `POSTGRES_*` / `SPRING_DATASOURCE_PASSWORD`. See AWS study §6.0c.

---

## 4. Target (must already exist)

| Piece | Value |
| --- | --- |
| Compute | **`asg-rest`**, private app subnets, estate default **desired=2**, InService, SSM Online |
| Ingress | **Internal** ALB `tg-rest` **:8080**. Never public |
| Data | SoR RDS `heavy_rental` on **:5432** (`sg-rest` → `sg-rds`). Haystack via **internal** Haystack ALB (`HAYSTACK_URL`, `sg-rest` → `sg-alb-haystack` **:8000**). REST does **not** open Bolt. Academy has **two** RDS; REST uses the SoR instance only. Haystack may still read SoR `:5432` for sync. |
| Secret | `heavy-rental/rest` (Postgres fields, Stripe **secret** + webhook + publishable, `HAYSTACK_URL`) |
| Limits | §6.4a: Tomcat `mem_limit: 1g`, `cpus: 1.0` on `t3.small` |

---

## 5. Discover EC2 + AWS CLI

Same pattern as Haystack CD. ASG name **`asg-rest`**. No public IPs. No instance IDs on the form.

```bash
aws sts get-caller-identity

aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names asg-rest \
  --query 'AutoScalingGroups[0].Instances[?LifecycleState==`InService`].InstanceId' \
  --output text
# Fail if missing / empty.

# SSM Online only
aws ssm describe-instance-information \
  --filters "Key=InstanceIds,Values=<id>" \
  --query 'InstanceInformationList[?PingStatus==`Online`].InstanceId'

aws secretsmanager describe-secret --secret-id heavy-rental/rest
# Do not echo SecretString.

# Compose on the instance (SSM send-command or Ansible aws_ssm):
#   get-secret-value heavy-rental/rest → .env
#   docker load < rest-api-*.tar.gz   OR  docker pull ghcr.io/...
#   compose up Tomcat :8080  mem_limit 1g cpus 1.0
#   curl -sfS http://127.0.0.1:8080/actuator/health || curl -sfS http://127.0.0.1:8080/
```

Optional read-only `terraform output` from **infra** state. Never `terraform apply`.

### 5.1 Runner vs instance (Academy three keys)

Credentials: **Academy / Vocareum** — paste the three keys on Run workflow (they change every Start Lab) or use Environment `academy`. **Paid** — OIDC only; **no** key fields. Region: `vars.AWS_REGION` or `us-east-1`. **CDK is not used.**

```
Runner (academy): AWS_ACCESS_KEY_ID + SECRET + SESSION_TOKEN
  → sts, describe-asg, ssm, describe-secret heavy-rental/rest, optional ECR push
Guest (LabRole): get-secret-value + docker load / ecr pull / HTTPS tar
Paid runner: OIDC only — fail if AWS_ACCESS_KEY_ID is set
```

AWS keys **do not** push GHCR (CI `GITHUB_TOKEN`). On **Academy**, paste the three keys on the form (or Environment fallback). **Never** on paid, on the EC2, or in Secrets Manager. Infra must have created `heavy-rental/rest` and filled `POSTGRES_*`, `HAYSTACK_URL`, and Stripe fields — this CD only reads them.

---

## 6. Secrets

| Store | REST app CD |
| --- | --- |
| GitHub `academy` | **Runner only:** three Vocareum keys + `AWS_REGION`. App passwords optional if SM is already filled |
| GitHub `paid` | **Runner only:** OIDC. No access keys |
| AWS `heavy-rental/rest` | **Instance (`LabRole`):** `POSTGRES_*` / `SPRING_DATASOURCE_*`, `HAYSTACK_URL`, `STRIPE_API_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PUBLISHABLE_KEY` |

Do not put `sk_` in the image. Do not use CI `REST_API_CLOUD_DB_*` as the RDS hostname — `sync-secrets` **builds** JDBC from Terraform + CD password. Fail deploy if `describe-secret` for `heavy-rental/rest` fails. See AWS study **§8.2** and **§8.7**.

---

## 7. Academy vs paid

| | Academy | Paid |
| --- | --- | --- |
| Workflow | `rest-api-cd-pipeline.example.yml` | `rest-api-cd-paid-pipeline.example.yml` |
| Auth | Vocareum three keys | OIDC |
| Image | Tar or ECR in-region | GHCR or paid ECR |
| If ASG missing | Fail | Fail |

---

## 8. Job graph

`action`: `deploy` | `configure-only` | `verify`

assert → discover (`asg-rest`) → resolve-image (CI tar / GHCR / **HTTPS tar URL**) → compose/ansible rest group → verify `:8080`. **No terraform.** `stop` / `destroy` stay on infra CD.

Image source is configured on the **GitHub Actions** form (`image_ref`, optional `image_http_url`) or Environment variable `IMAGE_HTTP_URL` — not hard-coded in Ansible. See [`../ANSIBLE-PROCESS.md`](../ANSIBLE-PROCESS.md) §3.1.

---

## 9. Checklist

**Live (branch 1):** discover `asg-rest` in [`../../heavy-rental-rest-api/deploy-pipeline/`](../../heavy-rental-rest-api/deploy-pipeline/). Example YAML **in this folder** stays fail-closed.

**Still stubs (REST app CD branch 2):** image pull/load + compose re-run from this CD. Infra first-compose (`guest_base` / `rest`) already exists. Delivery split: [`IMPLEMENTATION-PLAN.md`](IMPLEMENTATION-PLAN.md).

---

## 10. Pointers

- Estate: [`../AWS-INFRASTRUCTURE-FEASIBILITY.md`](../AWS-INFRASTRUCTURE-FEASIBILITY.md) §6 `asg-rest`, §6.0c, §6.4a, §7.2e
- Sibling app CD: [`../haystack-CD-feasibility/HAYSTACK-CD-FEASIBILITY.md`](../haystack-CD-feasibility/HAYSTACK-CD-FEASIBILITY.md), [`../web-portal-CD-feasibility/WEB-PORTAL-CD-FEASIBILITY.md`](../web-portal-CD-feasibility/WEB-PORTAL-CD-FEASIBILITY.md)
- Delivery split: [`IMPLEMENTATION-PLAN.md`](IMPLEMENTATION-PLAN.md)
- Live Academy skeleton: [`../../heavy-rental-rest-api/deploy-pipeline/`](../../heavy-rental-rest-api/deploy-pipeline/)
- CI: [`../../heavy-rental-rest-api/release-pipeline/`](../../heavy-rental-rest-api/release-pipeline/)
