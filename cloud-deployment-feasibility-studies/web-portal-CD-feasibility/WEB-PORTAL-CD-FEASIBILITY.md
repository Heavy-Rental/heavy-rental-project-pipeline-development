# Feasibility study: CD for heavy-rental-web-portal

## As-built (read this first)

This file is a **design record**. Living specs: [`../../heavy-rental-web-portal-pipeline/specification/`](../../heavy-rental-web-portal-pipeline/specification/). Folder index: [`../README.md`](../README.md).

| Study body (original) | As-built |
| --- | --- |
| GitHub Environment `paid` | **`AWS_ACTUAL`** (portal ADR 0009; infra ADR 0017) |
| `REST_BASE_URL` = internal REST ALB | **`http://<rest_alb_dns>:8080`** (internet-facing REST ALB, ADR 0018) |
| Paid portal CD later | **Delivered:** `portal-cd-paid-caller.yml` |
| GHCR `heavy-rental-web-portal` | **`ghcr.io/<owner>/heavy_rental_web_portal:<semver>`** + `:latest` |
| GHCR only off PR / published Release | Release is **`workflow_dispatch` only**; Publish always pushes public GHCR on success |

Portal ALB stays the only public **:80**. REST has its own public **:8080**. nginx `/api` still proxies.

**Status:** Study + as-built table. Example workflows are stubs.

**Destinations:** same two AWS accounts as [`../AWS-INFRASTRUCTURE-FEASIBILITY.md`](../AWS-INFRASTRUCTURE-FEASIBILITY.md) — **Academy** (Vocareum) and **Paid**. Separate GitHub Environments (`academy`, `AWS_ACTUAL`), separate callers. One run must never touch the other.

**This CD is manually triggered after the cloud estate is already up.** It does **not** create the VPC, `asg-portal`, the public portal ALB, or RDS. If `asg-portal` is missing, the run **fails** and the operator runs infra CD `action=apply` first. Live Academy workflow (discover **and** compose) is in `heavy-rental-web-portal-pipeline/deploy-pipeline/`. Infra **`apply`** still first-composes the portal. Infra **`configure-only`** does **not** compose the portal — use this app CD (or `apply` for first compose).

**The hard problem is not “how to start nginx.”** It is **how the runner learns which EC2s to deploy to** (private app subnets, no public IP, IPs change after Start Lab) **and** how a **static Vite SPA** talks to a **private** REST ALB without exposing REST or baking that URL into the public image.

---

## 1. Purpose and non-goals

### Purpose

Decide how **GitHub Actions** can **re-run the guest compose playbook** on an **already created** `asg-portal` EC2, using the **nginx:1.27-alpine + Vite `dist/` image** (CI Node **22**) portal CI Release already built. Infra CD Terraform created the instance; infra CD Ansible did the first compose (including the `/api` reverse-proxy). This pipeline is a **later, manual** compose run (new image only). No new EC2.

The Academy workflow (branch 1 discover + branch 2 compose) is in [`../../heavy-rental-web-portal-pipeline/deploy-pipeline/`](../../heavy-rental-web-portal-pipeline/deploy-pipeline/). Infra still does **first** compose on `apply`. This CD **re-runs** `guest_base` + `portal` for a new image or a secret refresh. See [`IMPLEMENTATION-PLAN.md`](IMPLEMENTATION-PLAN.md).

Portal is the **only public** ALB target. The browser talks to the public portal ALB. nginx on `asg-portal` proxies `/api` to the **internal** REST ALB. A Vite **dev server does not run in AWS**.

### Non-goals

- Rebuilding the SPA (`npm run build` / `tsc` / Vite), ESLint, Semgrep, CodeQL, or `docker build` from source
- `terraform apply` / creating AWS resources
- Deploying REST, Haystack, or Neo4j
- Running `vite` / `npm run dev` as the AWS process
- Putting REST or Haystack on the public ALB
- Putting `STRIPE_API_KEY` / `STRIPE_WEBHOOK_SECRET` on the portal or in the image
- Baking the **internal** REST ALB URL into a public GHCR / Vite `VITE_*` bundle
- Using portal CI (which has **no** `academy` / `paid` Environments) as CD auth

Infra, estate-wide secrets, and operate/stop live in the **AWS infrastructure** study and workflows.

---

## 2. Three pipelines (do not merge)

| Pipeline | Tree / file | Role |
| --- | --- | --- |
| **Portal CI** | `heavy-rental-web-portal-pipeline/` | Fast Feedback → Integration → **Release** (`dist/` zip + **Docker tar** + GHCR off PR) |
| **Infra CD** | `aws-infra-pipeline.example.yml` / paid | VPC, four ASGs, public portal ALB, internal REST/Haystack ALBs, RDS, secret **shells**, `sync-secrets`, `sync-ssh-keys` |
| **Portal app CD (this study)** | Live: `heavy-rental-web-portal-pipeline/deploy-pipeline/`. Examples in this folder stay stubs. | Manual deploy of **this** image onto existing `asg-portal` (`resolve-image` → Ansible `--limit portal` → SSM `GET /`). |

CI never applies AWS. Infra CD never rebuilds the SPA. App CD never creates the ASG.

### 2.1 Sequence (EC2 first, then compose, then image updates)

```
Infra CD  action=apply
    Terraform     →  creates asg-portal (EC2 InService)
    sync-secrets  →  heavy-rental/portal
                     (REST_BASE_URL + STRIPE_PUBLISHABLE_KEY)
    Ansible       →  first compose playbook on the guest
                     (Docker, .env, nginx :80 + /api → REST)

Later, when CI has a new image:
Portal app CD  (this study, workflow_dispatch only)
    discover      →  find existing InService+SSM EC2  (no terraform)
    compose       →  SAME guest playbook, portal group only
                     docker load/pull CI image
                     inject nginx /api proxy from REST_BASE_URL
                     compose up :80
```

Portal app CD **is** the compose playbook (Ansible or AWS CLI + SSM). It is **not** the Terraform step. It must not run unless that EC2 already exists.

---

## 3. What CI already produces

From [`../../heavy-rental-web-portal-pipeline/release-pipeline/release-pipeline.yml`](../../heavy-rental-web-portal-pipeline/release-pipeline/release-pipeline.yml):

| Artifact | When | How CD uses it |
| --- | --- | --- |
| Vite `dist/` zip `heavy-rental-web-portal-v{version}-build{run}-{sha}.zip` + stable `heavy-rental-web-portal-dist.zip` | Always on Packaging | Optional; image is enough. Zip has `index.html` at archive root (web-server document root) |
| Image tar `heavy-rental-web-portal-v{version}-build{run}-{sha}.tar.gz` | Always on Packaging | Academy-friendly: download + `docker load` on the instance (or copy to ECR in-region) |
| GHCR `ghcr.io/<owner>/heavy_rental_web_portal:<semver>` and `:latest` | Publish on `workflow_dispatch` | Academy and paid if GHCR pull works |

Image contract: **nginx:1.27-alpine** serving Vite `dist/` on **`:80`**, SPA `try_files $uri $uri/ /index.html`, hashed `/assets/` cached. Build does **not** start a Node/Vite process, REST, or Stripe. Release **must not** inline `VITE_*` lab URLs or `sk_` into `dist/` (ADR 0007). Stripe `pk_` is allowed.

CI-generated `nginx-spa.conf` (used when the app repo has no Dockerfile) has **SPA routing only**. It does **not** include `location /api`. App CD / infra first-compose **must** add that proxy on the guest (volume mount). See §5.6.

Specs: [`../../heavy-rental-web-portal-pipeline/specification/`](../../heavy-rental-web-portal-pipeline/specification/).

CI Environments: **none** for app config. Only `GITHUB_TOKEN` for GHCR. **No Stripe in CI.** Those names are **not** CD `academy` / `paid`. See AWS study §6.0c.

---

## 4. Target (must already exist)

| Piece | Value |
| --- | --- |
| Compute | Auto Scaling group **`asg-portal`** (private **app** subnets). Estate default **desired=2**, both **InService** |
| Ingress | **Public** ALB `tg-portal` **:80** (HTTPS `:443` only if an ACM cert exists). **Only** public target. HTTP :80 always |
| Egress to REST | Instance SG allows portal → **internal** REST ALB `tg-rest` **:8080** |
| Auth on instance | `LabInstanceProfile` (Academy) or paid instance profile. SSM agent up |
| Secret | `heavy-rental/portal` already filled by infra `sync-secrets` |
| Limits | AWS study §6.4a: nginx `mem_limit: 256m`, `cpus: 0.5` on `t3.micro` (~1 GiB). Leave 256–512 MiB for OS + SSM + Docker |

Portal compose on this ASG: **one nginx container**. **No** Tomcat, uvicorn, Neo4j, or Postgres.

---

## 5. The issue: data about the EC2 to deploy to

Portal instances have **no public IP** (they sit behind the public ALB). IDs and private IPs **change** on scale-replace and after Vocareum Start Lab. The operator must **not** paste instance IDs or SSH hosts on `workflow_dispatch` (they go stale; they are not secret-typed).

### 5.1 What the runner must learn

| Need | Why |
| --- | --- |
| Auto Scaling group name | Stable handle (`asg-portal`) |
| Instance IDs that are **InService** and **SSM Online** | Ansible / SSM target |
| Public portal ALB DNS | Operator-facing URL after verify (the **one** public name). Do not print instance IPs |
| Internal REST ALB DNS | Comes from `REST_BASE_URL` in `heavy-rental/portal`. Used by nginx, not by the browser |
| Confirmation `heavy-rental/portal` exists | `REST_BASE_URL` + `STRIPE_PUBLISHABLE_KEY` already there |

The runner does **not** need instance public IPs, SSH PEMs (everyday path is SSM), or Vocareum keys on the **instance**.

### 5.2 How to discover it (in order)

**1. Convention + AWS API (preferred)**  
Infra CD always names the group `asg-portal` (or a tagged name). After `assert-*`:

```bash
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names asg-portal \
  --query 'AutoScalingGroups[0].Instances[?LifecycleState==`InService`].InstanceId' \
  --output text

aws ssm describe-instance-information \
  --filters "Key=InstanceIds,Values=<id>" \
  --query 'InstanceInformationList[?PingStatus==`Online`].InstanceId'
```

If the ASG is missing, desired=0, or no instance is SSM Online → **fail** with “run infra CD apply / wait for Start Lab / run configure-only.” Do not invent hosts.

**2. Terraform outputs (optional cache)**  
Infra CD may write outputs (`asg_portal_name`, `alb_portal_dns`, `alb_rest_dns`) to the **infra** state. Portal CD may `terraform output -json` **read-only** against that state. It must **not** `apply`. If state is missing (lab reset), fall back to (1) + Secrets Manager for `REST_BASE_URL`.

**3. Secrets Manager (app data, not inventory)**  
`aws secretsmanager get-secret-value --secret-id heavy-rental/portal`  
Gives `REST_BASE_URL` and `STRIPE_PUBLISHABLE_KEY`. It does **not** replace ASG discovery. Infra `sync-secrets` must have run first. **Do not echo SecretString** in Actions logs.

**4. Tags (paid or if infra sets them)**  
`Role=portal`, `Project=heavy-rental`. Useful when the ASG name differs. Academy: still prefer the fixed name `asg-portal`.

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

Dynamic inventory, **one group** `portal`:

- `ansible_connection=amazon.aws.aws_ssm`
- `ansible_aws_ssm_instance_id=<id>` from §5.2
- No `ansible_host` public IP
- REST ALB is **not** in inventory; nginx reads `REST_BASE_URL` from the secret

SSH PEM (`heavy-rental/ssh/portal`) is **break-glass** only, and only after infra `sync-ssh-keys`. Deploy does not require it.

### 5.5 AWS CLI on the Actions runner

Credentials: **Academy / Vocareum** — paste the three keys on Run workflow (they change every Start Lab) or use Environment `academy`. **Paid** — OIDC only; **no** key fields. Region: `vars.AWS_REGION` or `us-east-1`. **CDK is not used.**

```bash
# 1. Prove the session (assert-lab / assert-account)
aws sts get-caller-identity

# 2. Find InService instance IDs (discover-targets)
IDS=$(aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names asg-portal \
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

# 4. Optional: public portal ALB DNS (this is the one URL operators may share)
aws elbv2 describe-load-balancers \
  --query "LoadBalancers[?contains(LoadBalancerName, 'portal')].DNSName" \
  --output text

# 5. App secret exists (do not echo SecretString in Actions logs)
aws secretsmanager describe-secret --secret-id heavy-rental/portal

# 6. Deploy (on the instance via SSM — not on the runner)
#    get-secret-value heavy-rental/portal → .env + nginx /api proxy
#    docker load < heavy-rental-web-portal-*.tar.gz
#       or: docker pull ghcr.io/<owner>/heavy_rental_web_portal:<tag>
#    docker compose up -d   # nginx :80; /api → REST_BASE_URL; NO vite

aws ssm send-command \
  --instance-ids "$ID" \
  --document-name AWS-RunShellScript \
  --parameters 'commands=["curl -sfS http://127.0.0.1:80/"]'
```

Step 6 **is** the compose playbook, implemented with **AWS CLI + SSM** (or Ansible `aws_ssm` — same job). It runs **on the existing EC2**, after infra created that instance. It writes/updates `.env` from `heavy-rental/portal`, writes the nginx `/api` snippet from `REST_BASE_URL`, loads the **CI** image, and `docker compose up` (nginx :80). It does **not** create the ASG.

Resource limits must match the AWS study **§6.4a** so a `t3.micro` portal host does not OOM:

| Service | `mem_limit` | `cpus` |
| --- | --- | --- |
| nginx (CI image) | `256m` | `0.5` |

Leave ~256–512 MiB for OS + SSM + Docker. `restart: unless-stopped`. **No** `replicas > 1` on one EC2.

**CI image:** Packaging in `heavy-rental-web-portal-pipeline/release-pipeline/` already builds a gzipped image tar; Publish pushes `ghcr.io/<owner>/heavy_rental_web_portal:<semver>`. This CD **must** `docker load` or `docker pull` that artifact. It **must not** `npm run build` or `docker build` from source.

### 5.6 Communication: public SPA, private REST (nginx `/api`, not Vite)

AWS study §6.6 Communication is still the contract:

```
Browser  →  public portal ALB :80/:443
              →  asg-portal  (nginx + Vite dist, :80)
                    nginx location /api  →  REST_BASE_URL
                                            (REST ALB :8080, internet-facing ADR 0018)
                                              →  asg-rest
```

| Claim | Valid? | Why |
| --- | --- | --- |
| Static Vite SPA interfaces the **public** ALB | **Yes** | Browser loads `index.html` + hashed assets from `tg-portal` :80 |
| Something on the portal host talks to the **internal** REST ALB | **Yes** | nginx on `asg-portal` `proxy_pass`es `/api` to `REST_BASE_URL` |
| A **Vite server** in AWS talks to REST | **No** | CI ships static `dist/` on nginx. `vite` / `npm run dev` is local only |
| Browser `fetch()` to the REST ALB DNS | **As-built: allowed** | ADR 0018 CORS includes portal + REST ALB. Do **not** bake that DNS into a Vite `VITE_*` bundle; prefer same-origin `/api` |
| REST on the **portal** ALB so the SPA can call it | **No** | Portal listener stays :80. REST has its **own** internet-facing ALB :8080 |

**Why CD must add the proxy.** CI `nginx-spa.conf` is:

```
listen 80;
root /usr/share/nginx/html;
location / { try_files $uri $uri/ /index.html; }
location /assets/ { … immutable cache … }
```

No `/api`. App CD (and infra first-compose) writes a guest snippet, for example:

```
# REST_BASE_URL from heavy-rental/portal (REST ALB, e.g. http://<rest-alb-dns>:8080)
location /api/ {
  proxy_pass         ${REST_BASE_URL}/;
  proxy_http_version 1.1;
  proxy_set_header   Host $host;
  proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header   X-Forwarded-Proto $scheme;
}
```

Mount that file over `/etc/nginx/conf.d/default.conf` (or `include` it) so a new CI image does not wipe the proxy. Fail compose if `REST_BASE_URL` is empty.

**`VITE_*` is bake-time.** Do not bake `REST_BASE_URL` into the public image. The browser calls **same-origin** `/api/...`. Optional later: a runtime `config.json` written from `STRIPE_PUBLISHABLE_KEY` (`pk_…` only) if the SPA must read Stripe in the browser. **Never** `sk_` or `whsec_`.

**Verify vs REST.** Portal health is `GET /` on `:80` (SPA `index.html`). A failing `/api` means REST is down or `REST_BASE_URL` is wrong — log it, do **not** fail portal `verify` solely because REST is down. REST has its own app CD.

---

## 6. Secrets (runtime)

| Store | Portal CD |
| --- | --- |
| GitHub Environment `academy` | **Runner only:** `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN` (+ `AWS_REGION`). Same names as infra CD |
| GitHub Environment `AWS_ACTUAL` | **Runner only:** OIDC `AWS_ROLE_TO_ASSUME`. **Fail** if `AWS_ACCESS_KEY_ID` is set |
| AWS `heavy-rental/portal` | What the **instance (`LabRole`)** reads: `REST_BASE_URL` (`http://<rest_alb_dns>:8080`), `STRIPE_PUBLISHABLE_KEY` (`pk_…` only) |

```
Runner (academy three keys) → sts, describe-asg, ssm, describe-secret, optional ECR push
Guest (LabRole)             → get-secret-value + docker load / ecr pull / HTTPS tar
```

AWS keys **do not** push GHCR (`GITHUB_TOKEN` / CI). On **Academy**, the three keys may be pasted on the form; **never** on paid, on the EC2, or in Secrets Manager. Infra Terraform **creates** the `heavy-rental/portal` shell; `sync-secrets` **must** write `REST_BASE_URL` + `pk_` before this CD runs. Fail if `describe-secret` misses the id.

Do **not** put `sk_` or `whsec_` in the image, in `heavy-rental/portal`, or in a Vite bundle. Those stay on `heavy-rental/rest`. Portal **CI** has no Stripe secrets. CD must **not** bake `REST_BASE_URL` into a public GHCR tag.

Inventory: AWS study **§6.0c** and **§8.7**. Portal CI uses **no** `academy`/`paid` secrets.

---

## 7. Academy vs paid

| | Academy | Paid |
| --- | --- | --- |
| Workflow | `portal-cd-academy-caller.yml` + reusable (example stub in this folder) | `portal-cd-paid-caller.yml` (same reusable) |
| Environment | `academy` | `AWS_ACTUAL` |
| Auth | Vocareum access key + session token | OIDC `AWS_ROLE_TO_ASSUME` |
| Image | Prefer **tar** or ECR in-region (LabRole pull-only on ECR) | GHCR or paid ECR |
| Connect | SSM + `LabInstanceProfile` | SSM + instance profile |
| Public URL | HTTP :80 on the portal ALB | HTTPS :443 when ACM exists; still portal-only |
| If ASG missing | Fail — do not create it | Same |

---

## 8. Job graph (manual)

```
Start Lab (Academy) → refresh academy secrets if needed
Infra CD already applied → asg-portal InService
        │
        ▼
Actions → Run workflow  (action + environment; optional image_ref)
        │
        ├─ assert-lab / assert-account     sts; refuse wrong account
        ├─ discover-targets                §5.2 — fail if no InService+SSM host
        ├─ resolve-image                   GHCR tag or download Release tar
        ├─ ansible-portal                  SSM; get-secret-value; /api proxy; compose up :80
        └─ verify                          curl GET / via SSM on :80
                                           (optional note public ALB DNS). Do not require /api.
```

| `action` | Jobs |
| --- | --- |
| `deploy` | assert → discover → resolve-image → ansible → verify |
| `configure-only` | assert → discover → ansible (same image, refresh proxy/secret) → verify |
| `verify` | assert → discover → health only |

**No terraform job.** `stop` / `destroy` stay on **infra** CD.

---

## 9. Maintainer checklist

**Enough from this study + AWS study to configure GitHub:**

- Environments `academy` / `paid` (same copy as infra CD)
- Copy example YAML into the CD repo
- Dispatch only after infra is up
- Do not type instance IDs
- Confirm `heavy-rental/portal` has `REST_BASE_URL` and `pk_…` only

**Live:** estate first-compose (`guest_base` / `portal`) **and** portal app CD branch 2 in [`../../heavy-rental-web-portal-pipeline/deploy-pipeline/`](../../heavy-rental-web-portal-pipeline/deploy-pipeline/) (same roles, `--limit portal`). Example YAML **in this folder** stays fail-closed.

**Paid/OIDC portal CD is delivered** (`portal-cd-paid-caller.yml`). Delivery split (Academy branches 1–2): [`IMPLEMENTATION-PLAN.md`](IMPLEMENTATION-PLAN.md).

---

## 10. Pointers

- Estate: [`../AWS-INFRASTRUCTURE-FEASIBILITY.md`](../AWS-INFRASTRUCTURE-FEASIBILITY.md) §6 (`asg-portal`, public `tg-portal`), §6.0c secrets, §6.4a limits, §6.6 Communication, §6.10 fallacies (topology **changes**), §7.2c, §7.2e
- Sibling app CD: [`../haystack-CD-feasibility/HAYSTACK-CD-FEASIBILITY.md`](../haystack-CD-feasibility/HAYSTACK-CD-FEASIBILITY.md), [`../rest-api-CD-feasibility/REST-API-CD-FEASIBILITY.md`](../rest-api-CD-feasibility/REST-API-CD-FEASIBILITY.md)
- CI: [`../../heavy-rental-web-portal-pipeline/release-pipeline/`](../../heavy-rental-web-portal-pipeline/release-pipeline/)
- Live Academy CD: [`../../heavy-rental-web-portal-pipeline/deploy-pipeline/`](../../heavy-rental-web-portal-pipeline/deploy-pipeline/)
- Delivery split: [`IMPLEMENTATION-PLAN.md`](IMPLEMENTATION-PLAN.md)
- Example workflows: [`web-portal-cd-pipeline.example.yml`](web-portal-cd-pipeline.example.yml), [`web-portal-cd-paid-pipeline.example.yml`](web-portal-cd-paid-pipeline.example.yml)
