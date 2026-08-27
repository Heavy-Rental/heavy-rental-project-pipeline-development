# Cloud-deployment feasibility studies

Design records for the Heavy Rental **estate** (VPC / ASGs / ALBs / RDS / Neo4j) and **app CD** (compose onto an already-created ASG).

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
| Portal → REST | nginx `/api` → internal REST ALB | nginx `/api` → `REST_BASE_URL=http://<rest_alb_dns>:8080` (public REST DNS). Browser may also call REST directly (CORS includes portal + REST ALB) |
| App CD paid callers | Later / not delivered | **Delivered:** `*-cd-paid-caller.yml` for Haystack, REST, and portal (same reusable as academy) |
| Release trigger | `develop`→`master` PR or published GitHub Release | **`workflow_dispatch` only.** Publish **creates** the GitHub Release |
| GHCR image names | hyphenated repo names | `haystack_recommender`, `heavy_rental_rest_api`, `heavy_rental_web_portal` (`:<semver>` + `:latest`) |
| REST CI `production` secrets | `REST_API_CLOUD_DB_*` | Same four names as Integration: `REST_API_DB_NAME` / `_USER` / `_PASSWORD` / `_PORT` (local Docker Postgres). CD does **not** use those names |
| Mobile | Unsigned APK, not in the VPC | Still not in the VPC. CI: Mockoon-required mocks; Release is dispatch-only + MobSF + GitHub Release (no GHCR) |
| Terraform remote lock | S3 + DynamoDB (older text) | S3 **`use_lockfile=true`** (no DynamoDB lock table) |
| NAT | Mixed NAT instance vs gateways in early sketches | **Two NAT Gateways** (one per public AZ). No NAT instance |

Mobile has **no app CD**. APK distribution is not an ASG.

## Files

| Path | Role |
| --- | --- |
| [`AWS-INFRASTRUCTURE-FEASIBILITY.md`](AWS-INFRASTRUCTURE-FEASIBILITY.md) | Estate design (Academy + paid). As-built table at the top |
| [`TERRAFORM-PROCESS.md`](TERRAFORM-PROCESS.md) | When infra CD runs Terraform |
| [`ANSIBLE-PROCESS.md`](ANSIBLE-PROCESS.md) | Guest compose (infra first-compose + app CD `--limit`) |
| [`haystack-CD-feasibility/`](haystack-CD-feasibility/) | Haystack app CD |
| [`rest-api-CD-feasibility/`](rest-api-CD-feasibility/) | REST app CD |
| [`web-portal-CD-feasibility/`](web-portal-CD-feasibility/) | Portal app CD |
| `*.example.yml` | Fail-closed sketches. Live workflows are in the infra project and each family’s `deploy-pipeline/` |

## What is still true

- CI builds images; CD does not `docker build` / `mvn` / `npm` on the guest.
- App CD never runs Terraform. Infra `apply` first-composes; infra `configure-only` does **not** compose portal / REST / Haystack images.
- Academy: Vocareum three keys on the **runner** only; guests use `LabRole` / `LabInstanceProfile`. Paid: OIDC; **no** Vocareum keys.
- Discover ASGs by name (`asg-portal` / `asg-rest` / `asg-haystack`). Do not type instance IDs on the form.
- Secrets Manager `heavy-rental/{portal,rest,haystack,neo4j}` is what the instance reads. `sk_` never lands on the portal.
