# Ansible process (feasibility studies)

**Status:** Contract. Live playbooks are in `heavy-rental-project-instructure-and-cloud-deploy` (`ansible/`) and each app family's `deploy-pipeline/ansible/`. Example YAML **in this folder** stays fail-closed. As-built index: [`README.md`](README.md).

**As-built:** paid GitHub Environment is **`AWS_ACTUAL`**. REST ALB is **internet-facing :8080**; portal nginx `/api` uses `REST_BASE_URL=http://<rest_alb_dns>:8080`. GHCR tags are `haystack_recommender`, `heavy_rental_rest_api`, `heavy_rental_web_portal`. App CD paid callers are delivered. Infra `apply` / `configure-only` run `configure.yml` (Docker + Neo4j); first-compose of portal / REST / Haystack is `deploy-projects` (`site.yml`) or app CD. ALB `tg-rest` / CD verify: `GET :8080/actuator/health` **2xx**. `tg-haystack` / CD verify: `GET :8000/health` **2xx**.

**Sources:** [`AWS-INFRASTRUCTURE-FEASIBILITY.md`](AWS-INFRASTRUCTURE-FEASIBILITY.md) §7.1a, §6.0c, §6.4a, §6.6; Haystack / REST / portal CD studies (same guest playbook, one group).

### Pinned versions (other project, 2026-08-17)

| Component | Version |
| --- | --- |
| Ansible community package | **14.3.1** (`ansible-core` **2.21.3**) |
| amazon.aws | **>=11.3.0,<12** (`common.text.converters`; connection `amazon.aws.aws_ssm`) |
| boto3 / botocore on the runner | **>=1.35.0** |
| Docker Compose on AL2023 | Try RPM `docker-compose-plugin`; else GitHub **v2.39.2** |

---

## 1. When Ansible runs

```
Infra CD  action=apply
    Terraform        →  EC2 InService (not Ansible)
    sync-secrets     →  fill Secrets Manager (not Ansible)
    sync-ssh-keys    →  PEMs after InService (not Ansible)
    Ansible          →  configure.yml (Docker all guests; Neo4j compose only)

Infra CD  action=configure-only
    sync-secrets + sync-ssh-keys + Ansible configure.yml
    (same as apply Ansible: Docker + Neo4j; no app images)

Infra CD  action=deploy-projects   (later workflow run)
    sync-secrets + sync-ssh-keys + image preflight + Ansible site.yml
    (portal + REST + Haystack + Neo4j + rds_logical)

Later, new CI image — app CD (workflow_dispatch):
    discover ASG → same playbook, one group only
    (portal | rest | haystack). No terraform. No neo4j group.
    Academy and paid callers.

Infra CD  action=stop | destroy
    No Ansible
```

---

## 2. How it connects

1. Actions runner installs Ansible (or uses an image that has it). Academy runner AWS creds: Vocareum form keys (masked via `$GITHUB_EVENT_PATH`) or Environment `academy` (not paid). Guest identity: **`LabInstanceProfile`** / **`LabRole`**.
2. Dynamic inventory: four groups — `portal`, `rest`, `haystack`, `neo4j`. Discover **all** InService + SSM Online instances (two per ASG at desired=2).
3. `ansible_connection=amazon.aws.aws_ssm`; instance id from the ASG. No public IP. `ansible_host` is the instance id.
4. RDS is **not** in inventory (no SSH guest OS).
5. Everyday path is SSM. SSH PEM (`heavy-rental/ssh/*`) is break-glass only.

---

## 3. Shared guest steps (every ASG)

1. Reach the instance via SSM (`LabInstanceProfile` / paid instance profile).
2. Install Amazon `docker`. Try `docker-compose-plugin`; if `docker compose version` fails, install Compose v2 from GitHub (AL2023 has no Docker CE repo).
3. `aws secretsmanager get-secret-value` of **that role’s** app secret only.
4. Map JSON → `.env`; `chmod 600`.
5. Do **not** copy GitHub `secrets.*` onto the guest. Do **not** fetch `sk_` or PEMs onto `asg-portal`.
6. Load or pull the **CI** image (see **§3.1**). Do not `docker build`, `npm run build`, or `mvn package`.
7. `docker compose up` with §6.4a `mem_limit` / `cpus`, `restart: unless-stopped`, no `replicas > 1`. Leave 256–512 MiB for OS + SSM + Docker.

### 3.1 Image source is configured on the GitHub Actions workflow

Ansible does **not** invent the URL. The **app CD** (or infra first-compose) job chooses the source and passes it as extra-vars. Configure it at the **pipeline** layer:

| Layer | Name | Role |
| --- | --- | --- |
| Environment **variable** `PORTAL_IMAGE` | Portal registry tag | Empty = stock `nginx`. Not a secret. |
| Environment **variable** `REST_IMAGE` / `HAYSTACK_IMAGE` | REST / Haystack tags | Empty = Run `image_ref`; still empty → that play fails |
| `workflow_dispatch` input `image_ref` | Registry tag | Infra: REST **and** Haystack fallback only (portal uses `PORTAL_IMAGE`). Portal **app** CD `action=deploy`: tag if `PORTAL_IMAGE` is empty. |
| `workflow_dispatch` input `image_http_url` | Optional HTTPS / `s3://` `.tar.gz` | `docker load` on **all** guests. Empty = `vars.IMAGE_HTTP_URL`. Leave empty for normal pulls. |

CI image names (Release; do not rebuild on the guest): portal **`nginx:1.27-alpine`** → `ghcr.io/<owner>/heavy_rental_web_portal` (Node **22** at build); REST **`tomcat:10.1-jdk21-temurin`** → `ghcr.io/<owner>/heavy_rental_rest_api` (Java **21**); Haystack **`python:3.12-slim-bookworm`** → `ghcr.io/<owner>/haystack_recommender`. Portal CD (`heavy-rental-web-portal-pipeline/deploy-pipeline/ansible/`) copies estate `guest_base` + `portal` and re-runs `--limit portal`. REST CD (`heavy-rental-rest-api/deploy-pipeline/ansible/`) copies estate `guest_base` + `rest` and re-runs `--limit rest`. Haystack CD (`haystack-fast-api-pipeline/deploy-pipeline/ansible/`) copies estate `guest_base` + `haystack` and re-runs `--limit haystack` (no Neo4j container). It does **not** replace infra first-compose (`action=deploy-projects` / `site.yml`). Infra `apply` does **not** compose portal / REST / Haystack.

Academy pull: public GHCR needs no login. ECR tags (`*.dkr.ecr.*`) get `aws ecr get-login-password` on the guest (`LabRole`). Private GHCR is **not** pulled (no token on the guest) — copy to ECR or load a tar. Prefer a **new tag** each redeploy (`compose up` does not `--pull always`).

**Academy preferred HTTP path:** HTTPS object in a **lab S3 bucket** (or S3 VPC endpoint). The runner or Vocareum user puts the CI tar there; the instance uses `LabRole` `GetObject`. Do **not** use a plain `http://` registry. GitHub Release HTTPS is allowed if NAT is up and auth is a secret, not a query string.

```yaml
# App CD workflow_dispatch (already has image_ref)
image_http_url:
  description: HTTPS URL of the CI image tar.gz (empty = Environment IMAGE_HTTP_URL or image_ref)
  required: false
  type: string
  default: ""
```

```bash
# Ansible on the guest when IMAGE_HTTP_URL is set
curl -fsSL -o /tmp/app.tar.gz "$IMAGE_HTTP_URL"
docker load < /tmp/app.tar.gz
```

Instance still needs outbound HTTPS (same-AZ NAT Gateway or S3 endpoint). Live `get_url` / `aws s3 cp` + `docker load` is in infra and app-CD `guest_base`.

---

## 4. Per-group compose (infra first run)

### 4.1 `portal` (`asg-portal`)

1. Read `heavy-rental/portal` → `REST_BASE_URL` + `STRIPE_PUBLISHABLE_KEY` + `VITE_STRIPE_PUBLISHABLE_KEY` (same `pk_`). Never `STRIPE_API_KEY`.
2. Write nginx `location /api/` → `REST_BASE_URL` (CI image has SPA `try_files` only). Fail if `REST_BASE_URL` is empty.
3. Compose **one** nginx on **:80**, `mem_limit: 256m`, `cpus: 0.5`.
4. Health: `GET /` on `:80`. Do not fail solely because `/api` (REST) is down.

### 4.2 `rest` (`asg-rest`)

1. Read `heavy-rental/rest` → `POSTGRES_*` / `SPRING_DATASOURCE_*` (plus `POSTGRES_HOSTNAME` / `POSTGRES_DB` / `POSTGRES_USER`), `HAYSTACK_BASE_URL`, Stripe secret + webhook + publishable.
2. Compose Tomcat on **:8080**, `mem_limit: 1g`, `cpus: 1.0`.
3. Health: wait for `GET :8080/actuator/health` **2xx** (ALB `tg-rest` matcher `200-299` on each instance IP). Do **not** use `GET /` — Spring Security returns **401**.
4. No Bolt. REST **guests** have no public IP; the REST **ALB** is internet-facing :8080 (ADR 0018).

### 4.3 `haystack` (`asg-haystack`)

1. Read `heavy-rental/haystack` → Haystack RDS Postgres fields plus app aliases `POSTGRES_HOSTNAME` / `POSTGRES_DB` / `POSTGRES_USER`, `DATABASE_URL`, `SOURCE_HOST` / `SOURCE_PORT` / `SOURCE_DATABASE` (SoR RDS), `TARGET_HOST` / `TARGET_PORT` / `TARGET_DATABASE` (Haystack RDS), `FLEET_BACKEND=sql`, `NEO4J_BACKEND=bolt`, `NEO4J_URI` (Bolt NLB, not localhost, not a guest private IP), optional `LLM_API_KEY`. Do not invent those **host** keys in the playbook. Alias worker credentials (`SOURCE_USER`, `TARGET_USER`, `PG*`, `NEO4J_POPULATE_TRIGGER_URL`) when SM omitted them (Haystack ADR 0011 / infra ADR 0020).
2. Compose:
   - uvicorn (CI image) **:8000** — `768m` / `1.0`
   - `postgres-haystack-sync` — `postgres:17` + `sync-from-primary.sh` — `256m` / `0.25`
   - `neo4j-populate` — `python:3.12-slim` + `populate_neo4j.py` — `256m` / `0.25`
3. **Must not** start a `neo4j` container. Do not start a pgvector container unless the Haystack RDS cannot load `vector` (credit fallback).
4. Sync `SOURCE_HOST` = SoR RDS endpoint. `TARGET_HOST` = Haystack RDS endpoint. Populate Bolt = NLB `NEO4J_URI`.
5. Health: wait for `GET :8000/health` **2xx** (ALB `tg-haystack` matcher `200-299` on each instance IP). Do **not** use `GET /` (404) or `/docs` as the ALB check.

### 4.4 `neo4j` (`asg-neo4j`) — infra / `configure-only` only

1. Read `heavy-rental/neo4j` → user / password.
2. Compose **only** `neo4j:5`, `/data` on EBS, `mem_limit: 4g`, `cpus: 1.5`, heap 512m–1G.
3. Bind Bolt on each guest. Haystack reaches them through the **internal NLB** (`bolt://<nlb-dns>:7687`). No public listener.
4. App CD does **not** run this group. Two guests are **not** a causal cluster.

---

## 5. RDS logical steps

Run via `delegate_to` a **rest** or **haystack** instance (those SGs can reach `:5432`). Do not `delegate_to` Neo4j. Do not open `:5432` to the Actions runner.

1. Terraform already created both instances (`heavy_rental` on SoR RDS, `haystack` on Haystack RDS). Do not invent a third DB for the sync worker.
2. Roles and grants on each instance.
3. `CREATE EXTENSION IF NOT EXISTS vector` on the Haystack RDS.
4. Credit fallback only: `CREATE DATABASE` on a single instance, or a pgvector container on `asg-haystack`.

---

## 6. App CD (same playbook, one group)

| Pipeline | Inventory group | Extra vs first compose |
| --- | --- | --- |
| Portal CD (`deploy-pipeline/ansible/`) | `portal` | New nginx + `dist/` image; keep `/api` proxy |
| REST CD (`deploy-pipeline/ansible/`) | `rest` | New Tomcat image; refresh `.env` from `heavy-rental/rest` |
| Haystack CD (`deploy-pipeline/ansible/`) | `haystack` | New uvicorn image; same `postgres:17` / `python:3.12-slim` workers (ADR 0011); still no neo4j |

Discover **every** `InService` + SSM Online instance in the ASG first (two at desired=2). Fail if the group is missing or none are Online.

---

## 7. Ansible must not

- Create the VPC, ASG, ALB, RDS **instance**, or IAM
- Put RDS in inventory as a host
- Open `:5432` to `0.0.0.0/0` or to the runner
- Start Neo4j on `asg-haystack`
- Put `STRIPE_API_KEY` on the portal
- Run on `action=stop` or `action=destroy`
- Mix CodeDeploy and Ansible on the same files without a split

---

## 8. Pointers

- Estate: [`AWS-INFRASTRUCTURE-FEASIBILITY.md`](AWS-INFRASTRUCTURE-FEASIBILITY.md) §7.1a, §6.4a, §6.0c
- [`haystack-CD-feasibility/HAYSTACK-CD-FEASIBILITY.md`](haystack-CD-feasibility/HAYSTACK-CD-FEASIBILITY.md)
- [`rest-api-CD-feasibility/REST-API-CD-FEASIBILITY.md`](rest-api-CD-feasibility/REST-API-CD-FEASIBILITY.md)
- [`web-portal-CD-feasibility/WEB-PORTAL-CD-FEASIBILITY.md`](web-portal-CD-feasibility/WEB-PORTAL-CD-FEASIBILITY.md)
