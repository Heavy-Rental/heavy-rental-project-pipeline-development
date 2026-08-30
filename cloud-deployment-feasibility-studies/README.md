# Cloud-deployment feasibility studies

Design records for the Heavy Rental **estate** (VPC / ASGs / ALBs / RDS / Neo4j), **app CD** (compose onto an already-created ASG), and a separate **EKS** assessment (the live infra pipeline does **not** create a cluster).

They are **not** the living specification. OpenSpec, OpenSPDD, and ADRs win if anything here disagrees.

| Living spec | Where |
| --- | --- |
| Estate (Terraform + Ansible + infra Actions) | [`../../heavy-rental-project-instructure-and-cloud-deploy/specification/`](../../heavy-rental-project-instructure-and-cloud-deploy/specification/) |
| App CI + CD families | [`../specification/`](../specification/) |

Conflict order: **OpenSpec scenarios → OpenSPDD Safeguards → ADR → YAML**. Example workflows in this folder are **fail-closed stubs**. Copy live YAML from the trees in the table, not from `*.example.yml`.

## As-built (what shipped)

Use this table instead of the original study body when the two disagree.

| Topic | Original study | As-built |
| --- | --- | --- |
| Paid GitHub Environment | `paid` | **`AWS_ACTUAL`** (S3 / SSM suffix `-actual`) |
| Infra Actions | One process or Environment pick | Two Actions, separate job graphs: `aws-infra-academy.yml` (`academy` + Vocareum), `aws-infra-paid.yml` (`AWS_ACTUAL` + OIDC) |
| REST ALB | Internal; no public 8080 | **Internet-facing :8080** in public subnets; `asg-rest` stays private (infra ADR 0018). Haystack ALB, Bolt NLB, and RDS stay internal |
| Portal → REST | nginx `/api` → internal REST ALB | nginx `/api` → `REST_BASE_URL=http://<rest_alb_dns>:8080` (public REST DNS; NAT hairpin). `sg-portal` egress TCP 8080 to `0.0.0.0/0`. Browser may also call REST directly (CORS includes portal + REST ALB) |
| App CD paid callers | Later / not delivered | **Delivered:** `*-cd-paid-caller.yml` for Haystack, REST, and portal (same reusable as academy) |
| Release trigger | `develop`→`master` PR or published GitHub Release | **`workflow_dispatch` only.** Publish **creates** the GitHub Release |
| GHCR image names | hyphenated repo names | `haystack_recommender`, `heavy_rental_rest_api`, `heavy_rental_web_portal` (`:<semver>` + `:latest`) |
| REST CI `production` secrets | `REST_API_CLOUD_DB_*` | Same four names as Integration: `REST_API_DB_NAME` / `_USER` / `_PASSWORD` / `_PORT` (local Docker Postgres). CD does **not** use those names |
| Mobile | Unsigned APK, not in the VPC | Still not in the VPC. CI: Mockoon-required mocks; Release is dispatch-only + MobSF + GitHub Release (no GHCR) |
| Terraform remote lock | S3 + DynamoDB (older text) | S3 **`use_lockfile=true`** (no DynamoDB lock table) |
| NAT | Mixed NAT instance vs gateways in early sketches | **Two NAT Gateways** (one per public AZ). No NAT instance |
| Guest count | Four ASGs at desired=2 = **8 EC2**; “do not add a 9th” | **9 EC2** (cap full): 8 app guests + single jump host **`hr-bastion`** (not an ASG). Infra ADR 0021 |
| Jump / SSH | SSM only; optional management SG; “never a lone `aws_instance`” | **`hr-bastion`** is the one standalone EC2 (public subnet, no ALB). App SGs allow `:22` only from `sg-bastion`. Everyday Ansible is still SSM. `stop` uses `stop-instances` on the bastion. `private_key_pem` is the **private** key; bastion gets hop + role private keys; app guests get the public line only |
| Infra Terraform | Four ASGs + ALBs + RDS | Same **plus** `aws_instance.bastion`, `sg-bastion`, shell `heavy-rental/ssh/bastion`, paid `hr-paid-bastion` |
| Infra `apply` compose | First-compose all four groups | `apply` / `configure-only` run **`configure.yml`** (Docker + **Neo4j only**). Portal / REST / Haystack first-compose is a later infra **`deploy-projects`** (`site.yml`) or app CD |
| CORS | Portal ALB origin only | `APP_CORS_ALLOWED_ORIGINS` = portal origin **and** `http://<rest_alb_dns>:8080` |
| REST ALB health | `GET /` (Spring 401) | `tg-rest` waits for `GET <instance>:8080/actuator/health` matcher **`200-299`** (2xx) |
| Haystack ALB health | `GET /` or `/docs` | `tg-haystack` waits for `GET <instance>:8000/health` matcher **`200-299`** (2xx) |
| Haystack sync/populate workers | `uv run python -m` on the uvicorn image | **`postgres:17` + `sync-from-primary.sh`** and **`python:3.12-slim` + `populate-neo4j-from-haystack.sh`** (wraps `populate_neo4j.py`; infra ADR 0020 / Haystack ADR 0011) |
| Portal health | `GET /` (unspecified matcher) | ALB `tg-portal` matcher **`200-399`**. App CD `verify` accepts **200 / 301 / 302** only (same path) |
| Portal CI Environments | None / no Stripe in CI | Fast Feedback and Integration CI have **no** Environment. **Release Packaging** uses Environment **`academy`** to bake Stripe `pk_` (`VITE_STRIPE_PUBLISHABLE_KEY`). CD auth is still a different use of `academy` / `AWS_ACTUAL` |
| EKS | Estate study Option B: allow-listed, not the default | **Recorded** in [`eks-feasibility/`](eks-feasibility/). Live `aws-infra-*.yml` **cannot** create EKS. A **new** Action **can** (Terraform + `LabEksClusterRole` for cluster **and** node, instance types nano–large). Ansible does **not** `CreateCluster`. VPC + ALB *graph* + two RDS **still apply**; four role ASGs **do not**. Do not stack on the **9-guest** compose estate |

Mobile has **no app CD**. APK distribution is not an ASG.

## Files

| Path | Role |
| --- | --- |
| [`AWS-INFRASTRUCTURE-FEASIBILITY.md`](AWS-INFRASTRUCTURE-FEASIBILITY.md) | Estate design (Academy + paid). As-built table at the top |
| [`TERRAFORM-PROCESS.md`](TERRAFORM-PROCESS.md) | When infra CD runs Terraform |
| [`ANSIBLE-PROCESS.md`](ANSIBLE-PROCESS.md) | Guest compose (infra `configure.yml` / `deploy-projects` `site.yml` + app CD `--limit`) |
| [`haystack-CD-feasibility/`](haystack-CD-feasibility/) | Haystack app CD |
| [`rest-api-CD-feasibility/`](rest-api-CD-feasibility/) | REST app CD |
| [`web-portal-CD-feasibility/`](web-portal-CD-feasibility/) | Portal app CD |
| [`eks-feasibility/`](eks-feasibility/) | Recorded EKS decisions (live pipeline / new Action / EC2+ALB+RDS). Index: [`eks-feasibility/README.md`](eks-feasibility/README.md) |
| `*.example.yml` | Fail-closed sketches. Live workflows are in the infra project and each family’s `deploy-pipeline/` |
| [`../docs/samples/github-oidc-app-cd.json`](../docs/samples/github-oidc-app-cd.json) | App-CD OIDC sketch (Environment `AWS_ACTUAL`; no `terraform apply`; no Vocareum keys) |

## What is still true

- CI builds images; CD does not `docker build` / `mvn` / `npm` on the guest.
- App CD never runs Terraform. Infra `apply` / `configure-only` run `configure.yml` (Docker + Neo4j only). Portal / REST / Haystack first-compose is infra `deploy-projects` (`site.yml`) or app CD.
- Academy: Vocareum three keys on the **runner** only; guests use `LabRole` / `LabInstanceProfile`. Paid: OIDC; **no** Vocareum keys.
- Discover app ASGs by name (`asg-portal` / `asg-rest` / `asg-haystack` / `asg-neo4j`). Do not type instance IDs on the form. Jump host is `hr-bastion` (`tag:Role=bastion`), not an ASG.
- Secrets Manager `heavy-rental/{portal,rest,haystack,neo4j}` is what the instance reads. `sk_` never lands on the portal.
- EKS is allow-listed (`LabEksClusterRole`, node class nano–large) and **out of scope** for the live `aws-infra-*.yml` pipeline. A **new** Action could create a cluster; do not add `aws_eks_*` to `terraform/academy/`. Details: [`eks-feasibility/EKS-FEASIBILITY.md`](eks-feasibility/EKS-FEASIBILITY.md) §2.1.
