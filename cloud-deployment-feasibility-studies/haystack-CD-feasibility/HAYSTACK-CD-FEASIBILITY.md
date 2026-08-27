# Feasibility study: CD for haystack-fast-api

## As-built (read this first)

This file is a **design record**. Living specs: [`../../haystack-fast-api-pipeline/specification/`](../../haystack-fast-api-pipeline/specification/). Folder index: [`../README.md`](../README.md).

| Study body (original) | As-built |
| --- | --- |
| GitHub Environment `paid` | **`AWS_ACTUAL`** (Haystack ADR 0010; infra ADR 0017) |
| Paid Haystack CD later | **Delivered:** `haystack-cd-paid-caller.yml` + shared reusable |
| GHCR `haystack-fast-api` | **`ghcr.io/<owner>/haystack_recommender:<semver>`** + `:latest` |
| GHCR only off PR / published Release | Release is **`workflow_dispatch` only**; Publish always pushes public GHCR on success |
| Example YAML is the workflow | Live: [`../../haystack-fast-api-pipeline/deploy-pipeline/`](../../haystack-fast-api-pipeline/deploy-pipeline/). Examples in this folder stay stubs |
| Infra `apply` first-composes Haystack | Infra **`apply` / `configure-only`** run `configure.yml` (Docker + Neo4j only). First-compose is infra **`deploy-projects`** (`site.yml`) or this app CD |
| Image tar `haystack-fast-api-v{version}-…` | Packaging artifact is **`haystack_recommender-image.tar.gz`** |

Haystack ALB stays **internal**. REST ALB is internet-facing :8080 (does not change Haystack CD).

**Status:** Study + as-built table. This file does not apply Terraform.

**Destinations:** same two AWS accounts as [`../AWS-INFRASTRUCTURE-FEASIBILITY.md`](../AWS-INFRASTRUCTURE-FEASIBILITY.md) — **Academy** (Vocareum) and **Paid**. Separate GitHub Environments (`academy`, `AWS_ACTUAL`), separate callers. One run must never touch the other.

**This CD is manually triggered after the cloud estate is already up.** It does **not** create the VPC, ASGs, ALBs, RDS, or Neo4j. If `asg-haystack` is missing (or no guest is InService), the run **fails** and the operator runs infra CD `action=apply` first. Infra leaves **desired=2**, a **Haystack RDS**, and `NEO4J_URI` pointing at the **Bolt NLB**. Live Academy workflow (discover **and** compose) is in `haystack-fast-api-pipeline/deploy-pipeline/`. Infra **`apply`** / **`configure-only`** do **not** compose Haystack (`configure.yml` is Docker + Neo4j only). First-compose is infra **`deploy-projects`** (`site.yml`) or this app CD. App-repo readiness: [`../../haystack-fast-api-pipeline/docs/PREPARE-HAYSTACK-REPO.md`](../../haystack-fast-api-pipeline/docs/PREPARE-HAYSTACK-REPO.md).

**The hard problem is not “how to start uvicorn.”** It is **how the runner learns which EC2s to deploy to** (private app subnets, no public IP, IPs change after Start Lab).

---

## 1. Purpose and non-goals

### Purpose

Decide how **GitHub Actions** can **re-run the guest compose playbook** on an **already created** `asg-haystack` EC2, using the **haystack-fast-api** image Haystack CI Release already built. Infra CD Terraform created the instance; infra CD Ansible did the first compose. This pipeline is a **later, manual** compose run (new image only). No new EC2.

The Academy workflow (branch 1 discover + branch 2 compose) is in [`../../haystack-fast-api-pipeline/deploy-pipeline/`](../../haystack-fast-api-pipeline/deploy-pipeline/). Infra still does **first** compose on `apply`. This CD **re-runs** `guest_base` + `haystack` (no Neo4j container). See [`IMPLEMENTATION-PLAN.md`](IMPLEMENTATION-PLAN.md).

### Non-goals

- Rebuilding the app, running Ruff/pytest, or `uv build`
- `terraform apply` / creating AWS resources
- Deploying portal, REST, or `asg-neo4j`
- Starting Neo4j on the Haystack host (default)
- Putting `LLM_API_KEY` in **CI** (Haystack CI must fail if that env is set)

Infra, estate-wide secrets, and operate/stop live in the **AWS infrastructure** study and workflows.

---

## 2. Three pipelines (do not merge)

| Pipeline | Tree / file | Role |
| --- | --- | --- |
| **Haystack CI** | `haystack-fast-api-pipeline/` | Fast Feedback → Integration → **Release** (wheel + **Docker tar** + GHCR off PR) |
| **Infra CD** | `aws-infra-pipeline.example.yml` / paid | VPC, four ASGs, ALBs, RDS, secret **shells**, `sync-secrets`, `sync-ssh-keys` |
| **Haystack app CD (this study)** | Live: `haystack-fast-api-pipeline/deploy-pipeline/`. Examples in this folder stay stubs. | Manual deploy of **this** image onto existing `asg-haystack` (`resolve-image` → Ansible `--limit haystack` → SSM `GET :8000/health` **2xx**). |

CI never applies AWS. Infra CD never rebuilds Haystack. App CD never creates the ASG.

### 2.1 Sequence (EC2 first, then compose, then image updates)

```
Infra CD  action=apply
    Terraform     →  creates asg-haystack (EC2 InService)
    sync-secrets  →  heavy-rental/haystack
    Ansible       →  first compose playbook on the guest
                     (Docker, .env, uvicorn + sync + populate)

Later, when CI has a new image:
Haystack app CD  (this study, workflow_dispatch only)
    discover      →  find existing InService+SSM EC2  (no terraform)
    compose       →  SAME guest playbook, haystack group only
                     docker load/pull CI image; compose up
```

Haystack app CD **is** the compose playbook (Ansible or AWS CLI + SSM). It is **not** the Terraform step. It must not run unless that EC2 already exists.

---

## 3. What CI already produces

From [`haystack-fast-api-pipeline/specification/pipelines/haystack-ci.md`](../../haystack-fast-api-pipeline/specification/pipelines/haystack-ci.md) and the Release pipeline:

| Artifact | When | How CD uses it |
| --- | --- | --- |
| Image tar `haystack-fast-api-v{version}-build{run}-{sha}.tar.gz` | Always on Packaging | Academy-friendly: download + `docker load` on the instance (or copy to ECR in-region) |
| GHCR `ghcr.io/<owner>/haystack_recommender:<semver>` and `:latest` | Publish on `workflow_dispatch` | Academy and paid if GHCR pull works. Release **creates** the GitHub Release; do not subscribe to `on: release` |
| Wheel / sdist | Always | **Not** required on EC2 if the image is used |

Image contract: **`python:3.12-slim-bookworm`** + uv + **uvicorn `app.main:app` on `:8000`** (`--extra neo4j`). GHCR `ghcr.io/<owner>/haystack_recommender`. Build does **not** start Postgres, Neo4j, or an LLM. Release **refuses** baked `POSTGRES_*` / `SOURCE_*` / `TARGET_*` and proves dummy runtime env (ADR 0008).

Runtime env (CD / Secrets Manager only): `POSTGRES_*` / `DATABASE_URL` (Haystack RDS), `SOURCE_*` (SoR / REST RDS), `TARGET_*` (Haystack RDS), `NEO4J_URI` / user / password, optional `LLM_API_KEY`. Not `bolt://neo4j:7687` and not localhost. Specs: [`../../haystack-fast-api-pipeline/specification/`](../../haystack-fast-api-pipeline/specification/).

---

## 4. Target (must already exist)

| Piece | Value |
| --- | --- |
| Compute | Auto Scaling group **`asg-haystack`** (private **app** subnets). Estate default **desired=2**, both **InService** |
| Ingress | Dedicated **internal** ALB `tg-haystack` **:8000**. Not on the public portal ALB |
| Data | **Haystack RDS** (`haystack`). Bolt via the **internal NLB** to `asg-neo4j` — workers on haystack, graph **not** on this host |
| Auth on instance | `LabInstanceProfile` (Academy) or paid instance profile. SSM agent up |
| Secret | `heavy-rental/haystack` already filled by infra `sync-secrets` |

Haystack compose on this ASG: **uvicorn + postgres-haystack-sync + neo4j-populate**. **No** `neo4j` container.

---

## 5. The issue: data about the EC2 to deploy to

Haystack instances have **no public IP**. IDs and private IPs **change** on scale-replace and after Vocareum Start Lab. The operator must **not** paste instance IDs or SSH hosts on `workflow_dispatch` (they go stale; they are not secret-typed).

### 5.1 What the runner must learn

| Need | Why |
| --- | --- |
| Auto Scaling group name | Stable handle (`asg-haystack`) |
| Instance IDs that are **InService** and **SSM Online** | Ansible / SSM target |
| Internal Haystack ALB DNS | Verify health; do not publish it |
| Confirmation `heavy-rental/haystack` exists | `NEO4J_URI` (Bolt NLB), Haystack RDS Postgres fields already there |

The runner does **not** need public IPs, SSH PEMs (everyday path is SSM), or Vocareum keys on the **instance**.

### 5.2 How to discover it (in order)

**1. Convention + AWS API (preferred)**  
Infra CD always names the group `asg-haystack` (or a tagged name). After `assert-*`:

```bash
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names asg-haystack \
  --query 'AutoScalingGroups[0].Instances[?LifecycleState==`InService`].InstanceId' \
  --output text

aws ssm describe-instance-information \
  --filters "Key=InstanceIds,Values=<id>" \
  --query 'InstanceInformationList[?PingStatus==`Online`].InstanceId'
```

If the ASG is missing, desired=0, or **no** instance is SSM Online → **fail** with “run infra CD apply / wait for Start Lab / run configure-only.” Desired=2 is the estate default; deploy **every** Online guest. Do not invent hosts.

**2. Terraform outputs (optional cache)**  
Infra CD may write outputs (`asg_haystack_name`, `alb_haystack_dns`, `rds_haystack_endpoint`, `neo4j_uri`) to the **infra** state. Haystack CD may `terraform output -json` **read-only** against that state. It must **not** `apply`. If state is missing (lab reset), fall back to (1).

**3. Secrets Manager (app data, not inventory)**  
`aws secretsmanager get-secret-value --secret-id heavy-rental/haystack`  
Gives `NEO4J_URI` (Bolt NLB), Haystack RDS Postgres, optional LLM. It does **not** replace ASG discovery. Infra `sync-secrets` must have run first.

**4. Tags (paid or if infra sets them)**  
`Role=haystack`, `Project=heavy-rental`. Useful when the ASG name differs. Academy: still prefer the fixed name `asg-haystack`.

### 5.3 What the operator types on Run workflow

| Input | Required | Notes |
| --- | --- | --- |
| `action` | Yes | `deploy` / `configure-only` / `verify` |
| `aws_environment` | Yes | `academy` or `AWS_ACTUAL` |
| `image_ref` | Optional | GHCR/ECR tag, or an `https://…` tar URL. Empty = latest Release tar / `:latest` |
| `image_http_url` | Optional | HTTPS URL of the CI `.tar.gz`. Empty = Environment `IMAGE_HTTP_URL`. Ansible `get_url` + `docker load` on the guest |
| `aws_access_key_id` / `aws_secret_access_key` / `aws_session_token` | Academy only | Vocareum AWS Details (change every Start Lab). Empty = Environment `academy`. **Do not add these on paid.** |

**Do not** add inputs for instance ID, private IP, or SSH host. Image source is a **pipeline** input/variable. Academy: prefer S3 HTTPS + `LabRole` GetObject. See [`../ANSIBLE-PROCESS.md`](../ANSIBLE-PROCESS.md) §3.1.

### 5.4 Ansible inventory

Dynamic inventory, **one group** `haystack`:

- `ansible_connection=amazon.aws.aws_ssm`
- `ansible_aws_ssm_instance_id=<id>` from §5.2
- No `ansible_host` public IP
- RDS is **not** in inventory; SQL stays `delegate_to` a haystack instance if needed

SSH PEM (`heavy-rental/ssh/haystack`) is **break-glass** only, and only after infra `sync-ssh-keys`. Deploy does not require it.

### 5.5 AWS CLI on the Actions runner

Credentials: **Academy / Vocareum** — paste the three keys on Run workflow (they change every Start Lab) or use Environment `academy`. **Paid** — OIDC only; **no** key fields. Region: `vars.AWS_REGION` or `us-east-1`. **CDK is not used.**

```bash
# 1. Prove the session (assert-lab / assert-account)
aws sts get-caller-identity

# 2. Find InService instance IDs (discover-targets)
IDS=$(aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names asg-haystack \
  --query 'AutoScalingGroups[0].Instances[?LifecycleState==`InService`].InstanceId' \
  --output text)
# Fail if Autoscale group missing, "None", or empty.

# 3. Keep only SSM Online
for id in $IDS; do
  aws ssm describe-instance-information \
    --filters "Key=InstanceIds,Values=${id}" \
    --query 'InstanceInformationList[?PingStatus==`Online`].InstanceId' \
    --output text
done
# Fail if none Online. Then: Start Lab, or infra configure-only.

# 4. Optional: internal Haystack ALB DNS (do not print as a public URL)
aws elbv2 describe-load-balancers \
  --query "LoadBalancers[?contains(LoadBalancerName, 'haystack')].DNSName" \
  --output text

# 5. App secret exists (do not echo SecretString in Actions logs)
aws secretsmanager describe-secret --secret-id heavy-rental/haystack

# 6. Deploy (on the instance via SSM — not on the runner)
#    get-secret-value heavy-rental/haystack → .env
#    docker load < haystack-fast-api-*.tar.gz
#       or: docker pull ghcr.io/<owner>/haystack_recommender:<tag>
#    docker compose up -d   # uvicorn :8000 + sync + populate; NO neo4j service

aws ssm send-command \
  --instance-ids "$ID" \
  --document-name AWS-RunShellScript \
  --parameters 'commands=["curl -sfS http://127.0.0.1:8000/health"]'
```

Step 6 **is** the compose playbook, implemented with **AWS CLI + SSM** (or Ansible `aws_ssm` — same job). It runs **on the existing EC2**, after infra created that instance. It writes/updates `.env` from `heavy-rental/haystack`, loads the **CI** image, and `docker compose up` (uvicorn :8000 + sync + populate; **no** neo4j). It does **not** create the ASG.

Resource limits must match the AWS study **§6.4a** so a `t3.small` haystack host does not OOM:

| Service | `mem_limit` | `cpus` |
| --- | --- | --- |
| uvicorn (CI image) | `768m` | `1.0` |
| postgres-haystack-sync | `256m` | `0.25` |
| neo4j-populate | `256m` | `0.25` |
| optional pgvector (fallback only) | `512m` / host **`t3.medium`** | `0.5` |

Leave ~256–512 MiB for OS + SSM + Docker. `restart: unless-stopped`.

**CI image:** Packaging in `haystack-fast-api-pipeline/` already builds a gzipped image tar; Publish pushes `ghcr.io/<owner>/haystack_recommender:<semver>`. This CD **must** `docker load` or `docker pull` that artifact. It **must not** `docker build` from source.

---

## 6. Secrets (runtime)

| Store | Haystack CD |
| --- | --- |
| GitHub Environment `academy` | **Runner only:** `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN` (+ `AWS_REGION`). Same names as infra CD. Not Stripe/DB unless infra has not synced yet |
| GitHub Environment `AWS_ACTUAL` | **Runner only:** OIDC `AWS_ROLE_TO_ASSUME`. **Fail** if `AWS_ACCESS_KEY_ID` is set |
| AWS `heavy-rental/haystack` | What the **instance** (`LabRole`) reads: Haystack RDS Postgres host/port/db/user/password/URL plus `POSTGRES_HOSTNAME` / `POSTGRES_DB` / `POSTGRES_USER`, `FLEET_BACKEND=sql`, `NEO4J_BACKEND=bolt`, `NEO4J_URI` (Bolt NLB)/`USER`/`PASSWORD`, optional `LLM_API_KEY` |

```
Runner (academy three keys) → sts, describe-asg, ssm, describe-secret, optional ECR push
Guest (LabRole)             → get-secret-value + docker load / ecr pull / HTTPS tar
```

AWS keys **do not** push GHCR (`GITHUB_TOKEN` / CI). On **Academy**, the three keys may be pasted on the form; **never** on paid, on the EC2, or in Secrets Manager. Infra Terraform **creates** the `heavy-rental/haystack` shell; `sync-secrets` **must** write the fields above before this CD runs. Fail if `describe-secret` misses the id.

Haystack **CI** must keep `LLM_API_KEY` unset. CD may write it to Secrets Manager; it must **not** bake it into the image.

Inventory: AWS study **§6.0c** and **§8.7**. Haystack CI uses **no** `academy`/`paid` secrets.

---

## 7. Academy vs paid

| | Academy | Paid |
| --- | --- | --- |
| Workflow | `haystack-cd-academy-caller.yml` + reusable (example stub: `haystack-cd-pipeline.example.yml`) | `haystack-cd-paid-caller.yml` (same reusable) |
| Environment | `academy` | `AWS_ACTUAL` |
| Auth | Vocareum access key + session token | OIDC `AWS_ROLE_TO_ASSUME` |
| Image | Prefer **tar** or ECR in-region (LabRole pull-only on ECR) | GHCR or paid ECR |
| Connect | SSM + `LabInstanceProfile` | SSM + instance profile |
| If ASG missing | Fail — do not create it | Same |

---

## 8. Job graph (manual)

```
Start Lab (Academy) → refresh academy secrets if needed
Infra CD already applied → asg-haystack InService
        │
        ▼
Actions → Run workflow  (action + environment; optional image_ref)
        │
        ├─ assert-lab / assert-account     sts; refuse wrong account
        ├─ discover-targets                §5.2 — fail if no InService+SSM host
        ├─ resolve-image                   GHCR tag or download Release tar
        ├─ ansible-haystack                SSM; get-secret-value; compose up :8000
        └─ verify                          curl health via SSM on :8000
                                           (or from a rest/haystack SG). No public URL.
```

| `action` | Jobs |
| --- | --- |
| `deploy` | assert → discover → resolve-image → ansible → verify |
| `configure-only` | assert → discover → ansible (same image) → verify |
| `verify` | assert → discover → health only |

**No terraform job.** `stop` / `destroy` stay on **infra** CD.

---

## 9. Maintainer checklist

**Enough from this study + AWS study to configure GitHub:**

- Environments `academy` / `paid` (same copy as infra CD)
- Copy example YAML into the CD repo
- Dispatch only after infra is up
- Do not type instance IDs

**Live:** estate first-compose (`guest_base` / `haystack`) **and** Haystack app CD branch 2 in [`../../haystack-fast-api-pipeline/deploy-pipeline/`](../../haystack-fast-api-pipeline/deploy-pipeline/) (same roles, `--limit haystack`, no Neo4j). Example YAML **in this folder** stays fail-closed.

**Paid/OIDC Haystack CD is delivered** (`haystack-cd-paid-caller.yml`). Delivery split (Academy branches 1–2): [`IMPLEMENTATION-PLAN.md`](IMPLEMENTATION-PLAN.md).

---

## 10. Pointers

- Estate: [`../AWS-INFRASTRUCTURE-FEASIBILITY.md`](../AWS-INFRASTRUCTURE-FEASIBILITY.md) §6 (`asg-haystack`), §6.0c secrets, §6.10 fallacies (topology **changes**), §7.2c, §7.2e
- Delivery split: [`IMPLEMENTATION-PLAN.md`](IMPLEMENTATION-PLAN.md)
- Live Academy CD: [`../../haystack-fast-api-pipeline/deploy-pipeline/`](../../haystack-fast-api-pipeline/deploy-pipeline/)
- CI + CD specs (OpenSpec / OpenSPDD / ADR): [`../../haystack-fast-api-pipeline/specification/`](../../haystack-fast-api-pipeline/specification/)
- Example workflows: [`haystack-cd-pipeline.example.yml`](haystack-cd-pipeline.example.yml), [`haystack-cd-paid-pipeline.example.yml`](haystack-cd-paid-pipeline.example.yml)
