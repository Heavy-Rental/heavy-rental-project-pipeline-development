# Feasibility study: CD for haystack-fast-api

**Status:** Study only. Example workflows are stubs. This file does not apply Terraform or deploy a live service.

**Destinations:** same two AWS accounts as [`AWS-INFRASTRUCTURE-FEASIBILITY.md`](AWS-INFRASTRUCTURE-FEASIBILITY.md) — **Academy** (Vocareum) and **Paid**. Separate GitHub Environments (`academy`, `paid`), separate workflows. One run must never touch the other.

**This CD is manually triggered after the cloud estate is already up.** It does **not** create the VPC, ASGs, ALBs, RDS, or Neo4j. If `asg-haystack` is missing, the run **fails** and the operator runs infra CD `action=apply` first.

**The hard problem is not “how to start uvicorn.”** It is **how the runner learns which EC2s to deploy to** (private app subnets, no public IP, IPs change after Start Lab).

---

## 1. Purpose and non-goals

### Purpose

Decide how **GitHub Actions** can **re-run the guest compose playbook** on an **already created** `asg-haystack` EC2, using the **haystack-fast-api** image Haystack CI Release already built. Infra CD Terraform created the instance; infra CD Ansible did the first compose. This pipeline is a **later, manual** compose run (new image only). No new EC2.

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
| **Haystack app CD (this study)** | `haystack-cd-pipeline.example.yml` / paid | Manual deploy of **this** image onto existing `asg-haystack` |

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

From [`haystack-fast-api-pipeline/specification/pipelines/haystack-ci.md`](../haystack-fast-api-pipeline/specification/pipelines/haystack-ci.md) and the Release pipeline:

| Artifact | When | How CD uses it |
| --- | --- | --- |
| Image tar `haystack-fast-api-v{version}-build{run}-{sha}.tar.gz` | Always on Packaging | Academy-friendly: download + `docker load` on the instance (or copy to ECR in-region) |
| GHCR `ghcr.io/<owner>/haystack-fast-api:<version>` and `:latest` | Published Release / non-PR only | Paid (and Academy if GHCR pull works). **Not** pushed on `develop`→`master` PR |
| Wheel / sdist | Always | **Not** required on EC2 if the image is used |

Image contract: Python 3.12 + uv + **uvicorn `app.main:app` on `:8000`**. Build does **not** start Postgres, Neo4j, or an LLM.

Runtime env (CD / Secrets Manager only): `POSTGRES_*` / `DATABASE_URL`, `NEO4J_URI` / user / password, optional `LLM_API_KEY`. Not `bolt://neo4j:7687` and not localhost.

---

## 4. Target (must already exist)

| Piece | Value |
| --- | --- |
| Compute | Auto Scaling group **`asg-haystack`** (private **app** subnets). Desired ≥ 1, **InService** |
| Ingress | Dedicated **internal** ALB `tg-haystack` **:8000**. Not on the public portal ALB |
| Data | RDS (Haystack DB or pgvector container on this ASG). **`asg-neo4j`** Bolt — workers on haystack, graph **not** on this host |
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
| Confirmation `heavy-rental/haystack` exists | `NEO4J_URI`, Postgres fields already there |

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

If the ASG is missing, desired=0, or no instance is SSM Online → **fail** with “run infra CD apply / wait for Start Lab / run configure-only.” Do not invent hosts.

**2. Terraform outputs (optional cache)**  
Infra CD may write outputs (`asg_haystack_name`, `alb_haystack_dns`, `rds_endpoint`) to the **infra** state. Haystack CD may `terraform output -json` **read-only** against that state. It must **not** `apply`. If state is missing (lab reset), fall back to (1).

**3. Secrets Manager (app data, not inventory)**  
`aws secretsmanager get-secret-value --secret-id heavy-rental/haystack`  
Gives `NEO4J_URI`, Postgres, optional LLM. It does **not** replace ASG discovery. Infra `sync-secrets` must have run first.

**4. Tags (paid or if infra sets them)**  
`Role=haystack`, `Project=heavy-rental`. Useful when the ASG name differs. Academy: still prefer the fixed name `asg-haystack`.

### 5.3 What the operator types on Run workflow

| Input | Required | Notes |
| --- | --- | --- |
| `action` | Yes | `deploy` / `configure-only` / `verify` |
| `aws_environment` | Yes | `academy` or `paid` |
| `image_ref` | Optional | GHCR tag or `latest`. Empty = latest Release tar / `:latest` |

**Do not** add inputs for instance ID, private IP, SSH host, or AWS keys.

### 5.4 Ansible inventory

Dynamic inventory, **one group** `haystack`:

- `ansible_connection=aws_ssm` (or `community.aws.aws_ssm`)
- `ansible_aws_ssm_instance_id=<id>` from §5.2
- No `ansible_host` public IP
- RDS is **not** in inventory; SQL stays `delegate_to` a haystack instance if needed

SSH PEM (`heavy-rental/ssh/haystack`) is **break-glass** only, and only after infra `sync-ssh-keys`. Deploy does not require it.

### 5.5 AWS CLI on the Actions runner

Credentials come from Environment **`academy`** (Vocareum three keys) or **`paid`** (OIDC). **Never** from `workflow_dispatch`. Region: `vars.AWS_REGION` or `us-east-1`. **CDK is not used.**

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
#       or: docker pull ghcr.io/<owner>/haystack-fast-api:<tag>
#    docker compose up -d   # uvicorn :8000 + sync + populate; NO neo4j service

aws ssm send-command \
  --instance-ids "$ID" \
  --document-name AWS-RunShellScript \
  --parameters 'commands=["curl -sfS http://127.0.0.1:8000/docs || curl -sfS http://127.0.0.1:8000/health"]'
```

Step 6 **is** the compose playbook, implemented with **AWS CLI + SSM** (or Ansible `aws_ssm` — same job). It runs **on the existing EC2**, after infra created that instance. It writes/updates `.env` from `heavy-rental/haystack`, loads the **CI** image, and `docker compose up` (uvicorn :8000 + sync + populate; **no** neo4j). It does **not** create the ASG.

Resource limits must match the AWS study **§6.4a** so a `t3.small` haystack host does not OOM:

| Service | `mem_limit` | `cpus` |
| --- | --- | --- |
| uvicorn (CI image) | `768m` | `1.0` |
| postgres-haystack-sync | `256m` | `0.25` |
| neo4j-populate | `256m` | `0.25` |
| optional pgvector | `512m` / host **`t3.medium`** | `0.5` |

Leave ~256–512 MiB for OS + SSM + Docker. `restart: unless-stopped`.

**CI image:** Packaging in `haystack-fast-api-pipeline/` already builds `haystack-fast-api-v…tar.gz` and (off PR) `ghcr.io/<owner>/haystack-fast-api:<version>`. This CD **must** `docker load` or `docker pull` that artifact. It **must not** `docker build` from source.

---

## 6. Secrets (runtime)

| Store | Haystack CD |
| --- | --- |
| GitHub Environment `academy` / `paid` | **Runner** AWS auth only (Vocareum keys vs OIDC). Optional `LLM_API_KEY` if infra did not sync it yet |
| AWS `heavy-rental/haystack` | What the **instance** reads: Postgres host/port/db/user/password/URL, `NEO4J_URI`/`USER`/`PASSWORD`, optional `LLM_API_KEY` |

Haystack **CI** must keep `LLM_API_KEY` unset. CD may write it to Secrets Manager; it must **not** bake it into the image.

Inventory of all Environment names: AWS study **§6.0c**. Haystack CI uses **no** `academy`/`paid` secrets.

---

## 7. Academy vs paid

| | Academy | Paid |
| --- | --- | --- |
| Workflow | `haystack-cd-academy.yml` (example: `haystack-cd-pipeline.example.yml`) | `haystack-cd-paid.yml` |
| Environment | `academy` | `paid` |
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

**Still stubs (other project):**

- Image pull/load onto the instance
- Ansible `haystack` playbook + §6.4a limits
- Health check command (`GET /docs` or `/health` as infra study)

Academy example YAML already has fail-closed discover (`asg-haystack` InService + SSM Online).

---

## 10. Pointers

- Estate: [`../AWS-INFRASTRUCTURE-FEASIBILITY.md`](../AWS-INFRASTRUCTURE-FEASIBILITY.md) §6 (`asg-haystack`), §6.0c secrets, §6.10 fallacies (topology **changes**), §7.2c, §7.2e
- CI: [`../../haystack-fast-api-pipeline/specification/pipelines/haystack-ci.md`](../../haystack-fast-api-pipeline/specification/pipelines/haystack-ci.md)
- Example workflows: [`haystack-cd-pipeline.example.yml`](haystack-cd-pipeline.example.yml), [`haystack-cd-paid-pipeline.example.yml`](haystack-cd-paid-pipeline.example.yml)
