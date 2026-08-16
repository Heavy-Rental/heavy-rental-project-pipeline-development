# Ansible process (feasibility studies)

**Status:** Contract only. Playbooks are not in this folder. Infra and app-CD example YAML `ansible` jobs are fail-closed stubs (`exit 1`).

**Sources:** [`AWS-INFRASTRUCTURE-FEASIBILITY.md`](AWS-INFRASTRUCTURE-FEASIBILITY.md) §7.1a, §6.0c, §6.4a, §6.6; Haystack / REST / portal CD studies (same guest playbook, one group).

---

## 1. When Ansible runs

```
Infra CD  action=apply
    Terraform        →  EC2 InService (not Ansible)
    sync-secrets     →  fill Secrets Manager (not Ansible)
    sync-ssh-keys    →  PEMs after InService (not Ansible)
    Ansible          →  first compose on all four groups

Infra CD  action=configure-only
    sync-secrets + sync-ssh-keys + Ansible   (no terraform apply)

Later, new CI image — app CD (workflow_dispatch):
    discover ASG → same playbook, one group only
    (portal | rest | haystack). No terraform. No neo4j group.

Infra CD  action=stop | destroy
    No Ansible
```

---

## 2. How it connects

1. Actions runner installs Ansible (or uses an image that has it). Academy runner AWS creds: Vocareum form keys or Environment `academy` (not paid).
2. Dynamic inventory: four groups — `portal`, `rest`, `haystack`, `neo4j`.
3. `ansible_connection=aws_ssm` (or `community.aws.aws_ssm`); instance id from the ASG. No public IP. No `ansible_host`.
4. RDS is **not** in inventory (no SSH guest OS).
5. Everyday path is SSM. SSH PEM (`heavy-rental/ssh/*`) is break-glass only.

---

## 3. Shared guest steps (every ASG)

1. Reach the instance via SSM (`LabInstanceProfile` / paid instance profile).
2. Install Docker and the compose plugin if missing.
3. `aws secretsmanager get-secret-value` of **that role’s** app secret only.
4. Map JSON → `.env`; `chmod 600`.
5. Do **not** copy GitHub `secrets.*` onto the guest. Do **not** fetch `sk_` or PEMs onto `asg-portal`.
6. Load or pull the **CI** image (see **§3.1**). Do not `docker build`, `npm run build`, or `mvn package`.
7. `docker compose up` with §6.4a `mem_limit` / `cpus`, `restart: unless-stopped`, no `replicas > 1`. Leave 256–512 MiB for OS + SSM + Docker.

### 3.1 Image source is configured on the GitHub Actions workflow

Ansible does **not** invent the URL. The **app CD** (or infra first-compose) job chooses the source and passes it as extra-vars. Configure it at the **pipeline** layer:

| Layer | Name | Role |
| --- | --- | --- |
| `workflow_dispatch` input `image_ref` | GHCR tag, ECR URI, or empty | Existing input |
| `workflow_dispatch` input `image_http_url` | Optional **HTTPS** URL of the CI `.tar.gz` | Empty = use Environment default or `image_ref` |
| Environment **variable** `IMAGE_HTTP_URL` | Default HTTPS tar URL for that `academy` / `paid` Environment | So operators do not retype it every run |
| Environment **secret** | Only if the URL needs a token (private GitHub Release). **Not** a public path | Never put a bearer token in the URL string |

Resolution order in `resolve-image` / Ansible:

1. Non-empty `inputs.image_http_url` → on the instance: `curl`/`ansible.builtin.get_url` → `docker load`
2. Else `vars.IMAGE_HTTP_URL` on the Environment → same
3. Else `inputs.image_ref` looks like `https://…` → treat as tar URL
4. Else `image_ref` is a registry tag → `docker pull` (paid GHCR/ECR; Academy only if pull works)
5. Else download the latest Release **tar** onto the runner and SSM/S3 it, then `docker load`

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

Instance still needs outbound HTTPS (NAT instance or S3 endpoint). Stubs stay fail-closed until the other project implements `get_url` + `docker load`.

---

## 4. Per-group compose (infra first run)

### 4.1 `portal` (`asg-portal`)

1. Read `heavy-rental/portal` → `REST_BASE_URL` + `STRIPE_PUBLISHABLE_KEY` only.
2. Write nginx `location /api/` → `REST_BASE_URL` (CI image has SPA `try_files` only). Fail if `REST_BASE_URL` is empty.
3. Compose **one** nginx on **:80**, `mem_limit: 256m`, `cpus: 0.5`.
4. Health: `GET /` on `:80`. Do not fail solely because `/api` (REST) is down.

### 4.2 `rest` (`asg-rest`)

1. Read `heavy-rental/rest` → `POSTGRES_*` / `SPRING_DATASOURCE_*`, `HAYSTACK_URL`, Stripe secret + webhook + publishable.
2. Compose Tomcat on **:8080**, `mem_limit: 1g`, `cpus: 1.0`.
3. Health: `GET /actuator/health` or `/`.
4. No Bolt. No public listener.

### 4.3 `haystack` (`asg-haystack`)

1. Read `heavy-rental/haystack` → Postgres fields, `NEO4J_URI` (private IP, not localhost), optional `LLM_API_KEY`.
2. Compose:
   - uvicorn (CI image) **:8000** — `768m` / `1.0`
   - `postgres-haystack-sync` — `256m` / `0.25`
   - `neo4j-populate` — `256m` / `0.25`
3. Optional pgvector container only on `t3.medium` (`512m` / `0.5`). Do not fit it on `t3.small`.
4. **Must not** start a `neo4j` container.
5. Sync `SOURCE_HOST` = RDS endpoint. Populate Bolt = `asg-neo4j`.
6. Health: `GET /docs` or `/health` on `:8000`.

### 4.4 `neo4j` (`asg-neo4j`) — infra / `configure-only` only

1. Read `heavy-rental/neo4j` → user / password.
2. Compose **only** `neo4j:5`, `/data` on EBS, `mem_limit: 4g`, `cpus: 1.5`, heap 512m–1G.
3. Bind Bolt to the instance private IP (`sg-haystack` only). No ALB.
4. App CD does **not** run this group.

---

## 5. RDS logical steps

Run via `delegate_to` a **rest** or **haystack** instance (those SGs can reach `:5432`). Do not `delegate_to` Neo4j. Do not open `:5432` to the Actions runner.

1. `CREATE DATABASE` `heavy_rental` if needed.
2. Create a Haystack database **only** if using the same RDS with a second db name (option B). Recommended Academy path is a pgvector **container** on `asg-haystack` instead.
3. Roles and grants.
4. `CREATE EXTENSION IF NOT EXISTS vector` when Haystack uses that RDS.

---

## 6. App CD (same playbook, one group)

| Pipeline | Inventory group | Extra vs first compose |
| --- | --- | --- |
| Portal CD | `portal` | New nginx + `dist/` image; keep `/api` proxy |
| REST CD | `rest` | New Tomcat image |
| Haystack CD | `haystack` | New uvicorn image; same sync + populate; still no neo4j |

Discover the ASG (`InService` + SSM Online) first. Fail if the group is missing.

---

## 7. Ansible must not

- Create the VPC, ASG, ALB, RDS **instance**, or IAM
- Put RDS in inventory as a host
- Open `:5432` to `0.0.0.0/0` or to the runner
- Start Neo4j on `asg-haystack`
- Put `STRIPE_SECRET_KEY` on the portal
- Run on `action=stop` or `action=destroy`
- Mix CodeDeploy and Ansible on the same files without a split

---

## 8. Pointers

- Estate: [`AWS-INFRASTRUCTURE-FEASIBILITY.md`](AWS-INFRASTRUCTURE-FEASIBILITY.md) §7.1a, §6.4a, §6.0c
- [`haystack-CD-feasibility/HAYSTACK-CD-FEASIBILITY.md`](haystack-CD-feasibility/HAYSTACK-CD-FEASIBILITY.md)
- [`rest-api-CD-feasibility/REST-API-CD-FEASIBILITY.md`](rest-api-CD-feasibility/REST-API-CD-FEASIBILITY.md)
- [`web-portal-CD-feasibility/WEB-PORTAL-CD-FEASIBILITY.md`](web-portal-CD-feasibility/WEB-PORTAL-CD-FEASIBILITY.md)
