# Feasibility study: AWS infrastructure for the Heavy Rental compose estate

**Destinations (two separate pipelines):**

1. **Academy** — [AWS Academy](https://awsacademy.instructure.com/) Learner Lab (Instructure + Vocareum sandbox)
2. **Paid** — a billed commercial AWS account (full IAM, OIDC, no Vocareum allow-list)

These are **different workflow files, GitHub Environments, Terraform states, and AWS accounts**. One run must never touch the other.

**Status:** Study only. No Terraform, CDK, or live AWS resources are created by this document.

**Sources:**

- [Heavy-Rental/heavy-rental-devcontainer-configuration](https://github.com/Heavy-Rental/heavy-rental-devcontainer-configuration) (`develop`) — Docker Compose stacks on the external `heavy-rental-network`
- This repo’s release pipelines — Docker images (and GHCR / image tar) for REST API, Haystack, and the web portal
- **Authoritative allow-list for this class:** [Vocareum Learner Lab Readme — Service usage and other restrictions](https://labs.vocareum.com/web/4955615/5650770.0/ASNLIB/public/docs/lang/en-us/README.html#services) (instructions dated 2025-06-24). Re-read it if Vocareum republishes.

---

## 1. Purpose and non-goals

### Purpose

Decide how **GitHub Actions** (the trigger) plus Terraform, Ansible, and the AWS CLI can stand up a **VPC that contains the Heavy Rental runtime**, and which AWS architecture fits:

1. The compose estate (shared network, three apps, two Postgres roles, Neo4j, sync/populate workers)
2. **CI** (existing app Release pipelines) **creates the Docker images**; **CD** (this study) deploys those images
3. **Two CD targets:** AWS Academy and a **paid** AWS account, each with its own Actions workflow
4. **CD** uses maintainer-copied GitHub Environments **`academy`** and **`paid`**. **CI** uses **other** names (`integration` / `production`) or **none** — inventory in **§6.0c**. They are not the same Environments.

### Non-goals

- Implementing live Terraform/Ansible or applying anything in a lab (example workflows are **fail-closed stubs**)
- A working CD repo — sketches and contracts only; the other project writes modules
- Lifting `sleep infinity` devcontainers into production
- Putting the Android APK in the VPC (store distribution, not a server)

Infrastructure, deploy, and operate belong to **another project**. This file is a decision record they can copy.

---

## 2. Verdict

| Question | Answer |
| --- | --- |
| Can we build this on this Vocareum lab? | **Yes.** The lab is **long-lived** (resources persist; EC2 is stopped at session end and restarted next Start Lab). Stay on the Readme allow-list and the credit budget. |
| EKS or simpler? | **Still simpler than EKS.** Prefer **VPC + four EC2 Auto Scaling groups + ALBs + one RDS**. REST and Haystack are **internal**; only the portal is public. RDS and Neo4j sit in a **separate private data-subnet pair**. |
| Ansible for EC2 + RDS sync? | **Yes — for configuration, not for creating the VPC/ASG/RDS.** Terraform creates ASGs, ALBs, the data subnets, and the database. Ansible installs Docker per ASG, writes env files, extensions, Neo4j on `asg-neo4j`, and Haystack sync/populate. |
| Dedicated ALB for REST? | **Yes — a dedicated internal ALB** (`scheme=internal`). REST is not on the public ALB. Same pattern as Haystack. |
| Recommended shape | **Academy (§6):** one VPC, three subnet tiers, four ASGs, one single-AZ RDS, one Neo4j. **Paid (§6P):** same tiers in a **separate** account; Multi-AZ RDS / second RDS / NAT Gateway / HTTPS optional. REST and Haystack: dedicated **internal** ALBs. No public 8080/8000/5432/7687. |
| CI vs CD | **CI** (this repo’s Release pipelines) **builds and publishes Docker images**. **CD** (this study — `aws-infra-academy.yml` / `aws-infra-paid.yml`) is the only apply path to AWS. CD does not rebuild the app. |
| GitHub Environments | The **maintainer** configures Environments **`academy`** and **`paid`** on the CD repo. CI trees use **other** Environments (`integration`, `production`) or **none**. Inventory: **§6.0c**. GitHub does not share Environments across repos. |
| Trigger / CD pipeline | **Academy CD:** Environment `academy` + Vocareum AWS keys. **Paid CD:** Environment `paid` + OIDC. Never one workflow for both accounts. |
| Primary IaC | **Terraform**, invoked **by that Actions workflow** (not CloudShell-first). |
| Config management | **Ansible**, invoked **by the same Actions workflow** after Terraform succeeds. |
| AWS CLI | Used **inside** the Actions job (`aws-actions/configure-aws-credentials` + CLI). Vocareum CloudShell is debug-only. |
| AWS CDK | Feasible only as a **CloudFormation generator**. Do not mix with Terraform. Many CDK constructs create IAM roles and will fail. |
| System design principles | Mapped in **§6.6**. Trade-offs in **§6.7**. Well-Architected in **§6.8**. Guidelines in **§6.9**. Deutsch fallacies in **§6.10**. Adherence review (what we keep vs accepted risk) in **§6.11**. |

Compose is the **requirement catalog**, not the AMI. Production-in-the-lab runs the **release images**, not the devcontainer `command: sleep infinity` services.

### 2.1 DevSecOps phases

Pipelines in this repo (and this CD study) line up with DevSecOps as follows. **Security is not a phase after Test** — SAST/SCA/CodeQL run in CI Test; CD adds isolation and Secrets Manager.

| Phase | What it means here | Where it lives |
| --- | --- | --- |
| **Plan** | Work intake and design. **Includes Jira** (epics/stories/bugs, sprint, traceability). OpenSpec / specification / SPDD for pipeline behaviour. | Jira (project board — not in this git tree). Specs: `haystack-fast-api-pipeline/openspec/`, `haystack-fast-api-pipeline/specification/`, `haystack-fast-api-pipeline/spdd/`; `heavy-rental-mobile/openspec/`, `heavy-rental-mobile/specification/`. REST and portal: YAML headers only. |
| **Code** | Feature branches in the application repos. | App git; no dedicated workflow. |
| **Build** | Checkout, toolchain, lock/sync, compile / Integration smoke. | Fast Feedback + Integration **Integration** job in all four CI families. |
| **Test** | QC (lint/unit) **and** Security Testing + CodeQL (+ mobile Mock Contract Tests). | Fast Feedback (Integration only). Integration CI and Release: QC, Security (Semgrep, Trivy, SCA), CodeQL. |
| **Release** | Versioned artifacts. **CI creates the Docker image** (except mobile APK). | Each app `release-pipeline/`. CD does **not** rebuild. |
| **Deploy** | **This study.** Terraform + `sync-secrets` + Ansible. Academy and paid CD workflows. Consumes CI images. Maintainer-copied GitHub Environments. | Other project: `aws-infra-academy.yml`, `aws-infra-paid.yml`. |
| **Operate** | Run/recover after go-live. Does **not** create infra. Needs infra knowledge. **SSM Session Manager** onto ASG instances (including **Haystack** and **Neo4j**). Lab `action=stop` (pause) or `action=destroy` (tear down Terraform). | Another project + AWS services below. Not CI. |
| **Monitor** | CloudWatch Logs/Alarms, SNS, CloudTrail, lab budget / Cost Explorer. | With Operate. CD may *create* log groups; **using** them is Operate/Monitor. |

#### Operate / Monitor — AWS services

These watch and recover what **Deploy** already built. They are not a third CD workflow.

| Phase | AWS service | Academy notes |
| --- | --- | --- |
| Operate | **Systems Manager Session Manager** | **Yes, including `asg-haystack` and `asg-neo4j`.** Same as portal and REST. Launch template uses **`LabInstanceProfile`** (`LabRole`). Amazon Linux has the SSM agent. **No SSH :22 and no public IP required** if the instance can reach SSM (`ssm`, `ssmmessages`, `ec2messages`) via a **NAT instance** (`t3.nano`) or **VPC interface endpoints**. Data-subnet Neo4j has no public IP — Session Manager is the only operate path. Do **not** add a NAT Gateway on Academy. Vocareum documents LabRole + Session Manager “terminal in the browser.” |
| Operate | ASG desired=0 / instance stop; **RDS stop** | `action=stop` on the CD workflow — lab-day cost control. Must include `asg-neo4j` and the RDS instance. Does **not** delete the VPC or ALBs. |
| Operate | **`terraform destroy`** | `action=destroy` on the **same** CD workflow — removes **every AWS resource Terraform created** in that state (VPC, ASGs, ALBs, RDS, secret shells, …). See **§7.2d**. |
| Monitor | **CloudWatch Logs** | ALB + instance/docker logs |
| Monitor | **CloudWatch Metrics + Alarms** | Public ALB 5xx, unhealthy targets, RDS CPU, EC2 status |
| Monitor | **SNS** | Alarm mail; do not expose REST/Haystack |
| Monitor (audit) | **CloudTrail** | Allowed; Vocareum: you **cannot** enable CloudWatch logging on the trail |
| Monitor (budget) | Learner Lab budget UI + **Cost Explorer** | Stop before credits disable the account |

**Not** for Academy Operate/Monitor: X-Ray, Managed Prometheus/Grafana, OpenSearch, EKS add-on monitoring.

**Haystack / Neo4j SSM contract:** Terraform attaches `LabInstanceProfile` on **every** ASG, including **`asg-haystack`** and **`asg-neo4j`**. Ansible/operators connect with `aws ssm start-session --target <instance-id>` or the console. Do not open 22, 8000, 7474, or 7687 to the internet to “get onto” Haystack or Neo4j. Neo4j Browser, if needed, is **SSM port-forward to 7474**, never a public listener. Each ASG’s SSH **private** key is in Secrets Manager (`heavy-rental/ssh/…`) for emergency SSH only (SSM port-forward to `:22`). Everyday operate is still Session Manager.

#### CI families (Build / Test / Release)

| App tree | Fast feedback | Integration CI | Release packaging |
| --- | --- | --- | --- |
| [`haystack-fast-api-pipeline/`](../haystack-fast-api-pipeline/) | Integration only | Integration → QC (Ruff/pytest) ∥ Security (Semgrep, pip-audit, Trivy) ∥ CodeQL | `uv build` + **Docker image** (tar / GHCR) |
| [`heavy-rental-rest-api/`](../heavy-rental-rest-api/) | Integration only | Integration → QC (Maven, Postgres) ∥ Security ∥ CodeQL | WAR + **Docker image** (Tomcat) |
| [`heavy-rental-web-portal-pipeline/`](../heavy-rental-web-portal-pipeline/) | Integration only | Integration → QC (ESLint/tsc) ∥ Security ∥ CodeQL | Vite `dist` zip + **nginx Docker image** |
| [`heavy-rental-mobile/`](../heavy-rental-mobile/) | Integration only | Integration → QC ∥ Security ∥ CodeQL ∥ **Mock Contract Tests** | Unsigned **APK** — **not** deployed to the AWS VPC |

Triggers stay GitHub Flow: feature push → Fast Feedback; PR/`develop` → Integration CI; `develop`→`master` or published Release → Release.

#### CD (Deploy only) — focus of this study

| Workflow | DevSecOps phase | Input |
| --- | --- | --- |
| `aws-infra-academy.yml` | **Deploy** | CI Docker images + Environment **`academy`** copy |
| `aws-infra-paid.yml` | **Deploy** | CI Docker images + Environment **`paid`** copy |

Jira tickets in **Plan** can link to CI checks and to a CD `workflow_dispatch` run; neither CI nor CD creates Jira issues.

---

## 3. What AWS Academy actually allows

Access path: Instructure course → **Start Lab** → Vocareum workbench → AWS Console. Identity is a federated `voclabs/…` principal, not an account you own.

This lab’s Readme (2025-06-24) is **broader** than older “Foundation Services” PDFs. Use the table below, not third-party summaries.

| Constraint | This Vocareum Readme | Impact |
| --- | --- | --- |
| Lifetime | **Long-lived.** Session timer ending keeps data; EC2 is stopped then **auto-started** on the next Start Lab | Design for stop/start. Elastic IP if you need a stable instance public IP. ALB DNS is stable. |
| Regions | **us-east-1** and **us-west-2** only | Pin Terraform `region` to `us-east-1` (`vockey` lives there). |
| Budget | Exceeding budget **disables the account and deletes everything** | Stop EC2/RDS when idle. Avoid NAT Gateway and EKS control plane. |
| IAM | **Cannot create users, groups, or roles** (service-linked roles only). Use **`LabRole`** / **`LabInstanceProfile`**. EKS uses pre-created **`LabEksClusterRole`** | No GitHub OIDC provider. Attach LabRole everywhere a service asks for a role. |
| EC2 | Quick Start / My / Community AMIs; **no Marketplace**. nano–**large**. ≤ **9** instances; ≤ **32** vCPU. ≥20 instances **wipes the account** | Docker on Amazon Linux (or another Quick Start Linux). App runtimes stay in **containers**. |
| RDS | PostgreSQL (and others). nano–**medium**. ≤ 100 GB gp2. **No enhanced monitoring**. **No Multi-AZ**. Lab may **not** stop RDS when the session ends | One small instance in a **private data-subnet group** (still **two AZs** — AWS requires that even when `multi_az = false`). `publicly_accessible = false`. Stop it yourself. AWS auto-starts a DB left stopped for 7 days. |
| ECS / Fargate | **Allowed.** Task role **and** execution role = **`LabRole`**. For ECS on EC2, create the ASG first (cannot create extra IAM roles) | Feasible, not required. Compose-on-EC2 is simpler and matches today’s network. |
| EKS | **Allowed** with **`LabEksClusterRole`** (cluster + node). Instance types nano–large | Feasible, still the wrong default for this estate (cost, IAM, ops). |
| ECR | Console user can **write**; **LabRole is read-only** | Push images as the Vocareum user. EC2 with LabRole can **pull**. |
| CodeDeploy | **Allowed** (can assume LabRole) | Optional alternative to Ansible for shipping bits to EC2. |
| Marketplace | Marketplace AMIs **not supported** | No Neo4j Marketplace AMI. The [Community Edition listing](https://aws.amazon.com/marketplace/pp/prodview-a5jr6bo72f5aw) (`prodview-a5jr6bo72f5aw`) is a CloudFormation stack (own VPC, public NLB/EIP, new IAM role) — **rejected on Academy**. Run `neo4j:5` as a **container** on `asg-neo4j` (Amazon Linux + `LabInstanceProfile`) in the **private data subnets**. See §6.2b. |

### 3.1 Session end does not freeze credits

**Yes — Learner Lab credits can still be deducted** after the Vocareum **lab session** stops, if billable resources are still there.

Ending the session is **not** a budget freeze and **not** a CloudFormation delete. This lab is **long-lived**: data and the VPC stay. Vocareum typically **stops EC2** (then **auto-starts** them on the next Start Lab). Anything that still has an hourly or storage price keeps consuming the budget. Exceeding it **disables the account and deletes everything**.

Intact ≠ free.

| Resource | After Vocareum session ends | Credit impact |
| --- | --- | --- |
| EC2 (four ASGs + NAT instance) | Usually **stopped** (not terminated) | **No** instance-hours while stopped. **Yes** EBS volumes (root + Neo4j `/data`) still bill. |
| **RDS Postgres** | Lab often **does not** stop it | **Yes — this is the usual leak.** A left-on `db.t3.micro` / `small` runs 24/7. |
| Public + internal **ALBs** | Left in place (`action=stop` does not delete them) | **Yes** — ALBs have an hourly charge even with no traffic. |
| VPC / subnets / SGs | Intact | No meaningful charge. |
| Secrets Manager / ECR images | Intact | Small ongoing storage. |
| NAT Gateway | **Not** in this design | Would bill 24/7 — that is why it is forbidden. |
| RDS after **`action=stop`** | **Stopped** | Compute stops; **storage** still bills. AWS **auto-starts** a DB left stopped for **7 days**. |

**Before you walk away:** GitHub Actions → this CD workflow → **`action=stop`**. That is the pipeline path that stops **RDS** (and ASGs if Vocareum has not already). Session end alone is not enough for RDS.

**Next Start Lab:** instances come back; re-run **`configure-only`**. Do not recreate RDS. Do not leave RDS running overnight “because the lab is stopped.”

`action=stop` is **pause** (credit control). It is **not** `terraform destroy`. ALBs, the VPC, secret shells, and RDS **storage** stay and still bill.

`action=destroy` is **teardown**. It runs `terraform destroy` against **that pipeline’s state** and deletes **every AWS resource Terraform created** (VPC, three subnet tiers, four ASGs, public + internal ALBs, RDS, NAT instance, secret shells, TF-owned ECR, …). Daily lab end is still `stop`. Use `destroy` at end of class, after a failed estate you want wiped, or when credits must go to zero. See **§7.2d**.

---

## 4. Current estate (requirements)

### 4.1 Shared network

Devcontainers join an **external** Docker network `heavy-rental-network` so REST, Haystack, and the portal can resolve each other by container name (`postgres-primary`, `postgres-haystack`, `neo4j`, …).

AWS equivalent: **one VPC**. Do not put apps in the default VPC and databases in another account or region.

### 4.2 Compose services → runtime need

From [heavy-rental-devcontainer-configuration](https://github.com/Heavy-Rental/heavy-rental-devcontainer-configuration):

| Compose service | Role | Must exist in the VPC? |
| --- | --- | --- |
| `heavy-rental-web-portal` | React SPA (dev); release image is **nginx + `dist/`** | Yes — HTTP |
| Spring REST API | Tomcat + WAR (release image) | Yes — HTTP + JDBC to primary Postgres |
| `postgres-primary` | System of record (`heavy_rental`) | Yes — not public |
| `haystack-fast-api` | FastAPI / uvicorn :8000 (release image) | Yes — HTTP + DB/Bolt |
| `postgres-haystack` | Postgres 17 + **pgvector**, Haystack R/W | Yes — not public |
| `postgres-haystack-sync` | Polls primary → merge into Haystack DB (~60s) | Yes — worker, no public port |
| `neo4j` | Bolt 7687 / Browser 7474 | Yes — Bolt **private**, in the **data subnet** (not on the Haystack host) |
| `neo4j-populate` | SQL → Cypher; HTTP :8089 | Yes — worker on `asg-haystack`; HTTP internal only |

REST also documents a **read-replica** compose variant. Academy **forbids Multi-AZ RDS**. Do **not** implement a replica in the lab.

### 4.3 What Release already produces

| App | Image | Port |
| --- | --- | --- |
| REST API | `tomcat:10.1-jdk21` + `ROOT.war` → GHCR / `.tar.gz` | 8080 |
| Haystack | Python 3.12 + uv + uvicorn `app.main:app` | 8000 |
| Web portal | nginx serving Vite `dist/` | 80 |

A later deploy project loads those images (ECR copy or `docker load` of the tar). It does not rebuild from source on EC2.

Haystack **app** CD (manual, after this estate exists): [`haystack-CD-feasibility/HAYSTACK-CD-FEASIBILITY.md`](haystack-CD-feasibility/HAYSTACK-CD-FEASIBILITY.md). REST **app** CD: [`rest-api-CD-feasibility/REST-API-CD-FEASIBILITY.md`](rest-api-CD-feasibility/REST-API-CD-FEASIBILITY.md). Portal **app** CD: [`web-portal-CD-feasibility/WEB-PORTAL-CD-FEASIBILITY.md`](web-portal-CD-feasibility/WEB-PORTAL-CD-FEASIBILITY.md) (public ALB only; nginx `/api` → internal REST ALB). Each discovers its ASG via the AWS API — they do not create EC2.

---

## 5. Architecture options

### A. VPC + four ASGs + public portal ALB + internal REST/Haystack ALBs + RDS in a data subnet — **recommended**

Maps `heavy-rental-network` onto separate scale groups **and** a dedicated **private data-subnet pair**. Only the portal is public. IAM stays on `LabRole`. Images from ECR or GHCR tar. RDS and Neo4j are **not** in the same subnets as the app ASGs. This topology is allowed on Academy (plain VPC/EC2/RDS; no extra IAM roles).

### B. Amazon EKS

**Allowed on this lab** (`LabEksClusterRole` for cluster and node; node instance class nano–large). Still **not recommended**.

- Control plane + nodes + typically a NAT or public nodes will consume the budget faster than one EC2 + RDS
- You still cannot create extra IAM roles (IRSA, load-balancer controller, etc.)
- Three release images and two workers do not need Kubernetes scheduling

Revisit EKS only if a course rubric requires it or the service count jumps.

### C. ECS on Fargate (or ECS on EC2)

**Allowed on this lab** if every task uses **`LabRole` as both task role and execution role**. For ECS on EC2, create the Auto Scaling group first so ECS does not try to create a new role.

Still **not the default**: you would rewrite compose as task definitions, split the sync/populate workers, and fight LabRole-only IAM. Compose-on-EC2 is the same topology you already run.

### D. One public EC2, no ALB, Postgres in Docker

**Feasible fallback** if credits are tight. Weaker isolation and **exposes too much** if 8080/8000 are opened. Not the target. If used at all, still do not publish REST or Haystack to the internet.

### E. Elastic Beanstalk Docker / App Runner

Beanstalk **is** listed (use `LabRole` + `LabInstanceProfile`). It is a poor match for **three images + Neo4j + two workers + two data stores** on one environment. App Runner is **not** listed. Skip as the primary design.

---

## 6. Recommended architecture (AWS Academy)

This section is the **lab** design. REST and Haystack are **internal servers**. Only the Vite/nginx **portal** is internet-facing. The **paid** account is a **separate VPC** with the same three tiers plus extras — see **§6P**.

Two AZs of **subnets**. **One** RDS. **One** Neo4j. Academy **forbids Multi-AZ RDS**. A subnet in each AZ is not a database in each AZ.

```
                         Internet
                             │
                      Internet Gateway (IGW)
                             │
         ┌───────────────────┴──────────────────────────────────────────────┐
         │                     VPC  us-east-1  (Academy)                    │
         │                                                                  │
         │   public subnets                                                 │
         │   AZ-a 10.0.0.0/24              AZ-b 10.0.1.0/24                 │
         │   ┌─────────────────────────────┬─────────────────────────────┐  │
         │   │         Public ALB (spans both)  portal :80 only          │  │
         │   │         NO /api  NO /haystack  NO 5432  NO 7687           │  │
         │   └──────────────┬──────────────┴─────────────────────────────┘  │
         │                  │ target :80                                    │
         │   private APP subnets                                            │
         │   AZ-a 10.0.10.0/24             AZ-b 10.0.11.0/24                │
         │   ┌─────────────────────────────┬─────────────────────────────┐  │
         │   │ ASG portal  nginx :80       │  (ASG may land in either AZ;│  │
         │   │ Internal ALB REST :8080     │   desired=1 → one instance) │  │
         │   │ Internal ALB Haystack :8000 │                             │  │
         │   │ ASG rest Tomcat:8080 ──────►│ ASG haystack uvicorn:8000   │  │
         │   │                             │ + sync + populate           │  │
         │   │                             │ (no Neo4j on haystack)      │  │
         │   └──────────────┬──────────────┴──────────────┬──────────────┘  │
         │                  │ JDBC                        │ Bolt / JDBC     │
         │                  ▼                             ▼                 │
         │   private DATA subnets  — no IGW, no public IPs                  │
         │   AZ-a 10.0.20.0/24             AZ-b 10.0.21.0/24                │
         │   ┌─────────────────────────────┬─────────────────────────────┐  │
         │   │ ONE RDS Postgres :5432      │ empty capacity              │  │
         │   │   multi_az=false            │ (required in subnet group;  │  │
         │   │ ONE asg-neo4j  neo4j:5      │  not a second RDS/Neo4j)    │  │
         │   │   Bolt :7687  max=1         │                             │  │
         │   │ (RDS and Neo4j each sit in  │                             │  │
         │   │  one AZ, not both)          │                             │  │
         │   └─────────────────────────────┴─────────────────────────────┘  │
         └──────────────────────────────────────────────────────────────────┘
```

\*Public ALB stays **HTTP :80** unless the class already has a domain + ACM cert. REST, Haystack, RDS, and Neo4j **never** get a public listener. RDS and Neo4j may share AZ-a, or one may land in AZ-b — still **one of each**.

### 6.0 Internal servers (REST + Haystack)

Neither the Spring Boot REST API nor Haystack may be reached from the internet.

| Path | Allowed? |
| --- | --- |
| Public ALB rule to REST (`/api`) or Haystack (`/haystack`) | **No** |
| Dedicated **internet-facing** ALB for REST or Haystack | **No** |
| Instance SG 8080 or 8000 from `0.0.0.0/0` or `sg-alb-public` | **No** |
| Browser / mobile calling REST or Haystack directly | **No** — browser talks to the **portal** only; portal calls REST on the **internal** REST ALB; REST calls Haystack on the **internal** Haystack ALB (or compose DNS if they share a host) |
| **Dedicated internal ALB** for REST (`scheme=internal`, `tg-rest` :8080) | **Yes** |
| **Dedicated internal ALB** for Haystack (`scheme=internal`, `tg-haystack` :8000) | **Yes** |
| SSM port-forward for a student demo | **Yes** — break-glass, not ingress |

**Can REST have its own dedicated ALB?** Yes. It **should** — a **dedicated internal** ALB, not a public one. Same for Haystack. Do not share the public portal ALB with either API.

If lab credits cannot afford two internal ALBs, collapse REST+Haystack onto **one** internal ALB with two target groups. **Never** put either API on the public ALB.

### 6.0a Every EC2 is in an Auto Scaling group

There is **no standalone EC2**. Each compute role is a launch template + Auto Scaling group (EC2 Auto Scaling is on the Vocareum allow-list). Attach `LabInstanceProfile` on the launch template.

| ASG | Subnet tier | What runs | Registers with | Academy size |
| --- | --- | --- | --- | --- |
| `asg-portal` | Private **app** | nginx portal image | **Public** ALB `tg-portal` :80 | min 1, desired 1, max 2 |
| `asg-rest` | Private **app** | Tomcat + WAR | **Internal** REST ALB `tg-rest` :8080 | min 1, desired 1, max 2 |
| `asg-haystack` | Private **app** | uvicorn Haystack + sync + populate (+ optional pgvector container). **No Neo4j.** | **Internal** Haystack ALB `tg-haystack` :8000. SSM via `LabInstanceProfile`. | min 1, desired 1, max 2 |
| `asg-neo4j` | Private **data** | `neo4j:5` container only | **None** (no ALB on Academy). SSM via `LabInstanceProfile`. Bolt from `sg-haystack` only. | min 1, desired 1, **max 1** |

Hard caps still apply across **all** ASGs: ≤ **9** instances, ≤ **32** vCPU, class ≤ **large**. Default desired=1 on each of the **four** ASGs so the lab stays at four instances (five if a `t3.nano` NAT instance is used). That is inside the Vocareum cap.

ASG health: ELB health checks on portal / REST / Haystack so an unhealthy node is replaced. **`asg-neo4j` uses EC2 health only** (no ELB) and **scale-in protection** — it is stateful. Scale policies stay **off** (no CPU scale-out that burns credits).

RDS is not EC2 — no ASG. Neo4j is a container on **`asg-neo4j` in the data subnets**, not a sidecar on Haystack. Marketplace AMI is forbidden, so the host is Amazon Linux + Docker + `LabInstanceProfile`. Neo4j is **derived state** (SQL → Cypher via `neo4j-populate`); if the instance is replaced, Ansible re-pulls `neo4j:5` and the populate worker rebuilds the graph from RDS.

### 6.0c Credentials live in AWS Secrets Manager

**GitHub Environment secrets stay required for the CI pipeline and for `sync-secrets`.** They are not what the EC2s read at runtime.

| Store | Who writes | Who reads | What |
| --- | --- | --- | --- |
| GitHub Environment **`academy`** | Human (or secret admin) | **GitHub Actions only** | Vocareum AWS keys + app / Stripe / SSH public material |
| **AWS Secrets Manager** | **`sync-secrets`** (app / Postgres / Stripe) and **`sync-ssh-keys`** (PEMs **after** InService) | Instances: app JSON via `LabRole`. Configurer: SSH PEMs. | App JSON per ASG; SSH PEMs only after EC2 exists |

**The pipeline updates AWS Secrets from the secrets it has** plus Terraform outputs (RDS hostname, ALB DNS, Neo4j Bolt URI). Ansible and user-data **only retrieve** from Secrets Manager. Do not scp `.env` or PEMs from the runner onto disk in git. Do not embed passwords in launch templates.

Never put Vocareum `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_SESSION_TOKEN` into Secrets Manager. Those exist only so the Academy **runner** can call AWS.

#### App secrets (one JSON per ASG)

| Secrets Manager id | ASG | JSON fields |
| --- | --- | --- |
| `heavy-rental/portal` | `asg-portal` | `REST_BASE_URL` (internal REST ALB Terraform output). **Stripe (portal):** `STRIPE_PUBLISHABLE_KEY` (from GitHub Environment). **Never** `STRIPE_SECRET_KEY` or `STRIPE_WEBHOOK_SECRET` on the portal — those are REST-only. |
| `heavy-rental/rest` | `asg-rest` | **Postgres (all of):** `POSTGRES_HOST` (RDS endpoint hostname from Terraform — data-subnet address, not public), `POSTGRES_PORT` (`5432`), `POSTGRES_DATABASE` (`heavy_rental`), `POSTGRES_USERNAME`, `POSTGRES_PASSWORD`, `POSTGRES_URL` / `SPRING_DATASOURCE_URL` (`jdbc:postgresql://<host>:<port>/<database>`). Also `SPRING_DATASOURCE_USERNAME` / `SPRING_DATASOURCE_PASSWORD` (same user/password). `HAYSTACK_URL` (internal Haystack ALB). **Stripe (REST):** `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PUBLISHABLE_KEY` (same publishable key as the portal). |
| `heavy-rental/haystack` | `asg-haystack` | Same Postgres **field set** for the Haystack DB (same RDS host/port on Academy; `POSTGRES_DATABASE` may be the Haystack db name). `DATABASE_URL` (`postgresql://user:pass@host:port/db`). `NEO4J_URI` (from `asg-neo4j` private IP, e.g. `bolt://10.0.20.x:7687` — not localhost), `NEO4J_USER`, `NEO4J_PASSWORD`, `LLM_API_KEY` if used. No Stripe. |
| `heavy-rental/neo4j` | `asg-neo4j` | `NEO4J_USER`, `NEO4J_PASSWORD`. No Postgres password dump, no Stripe, no LLM key. |

Terraform **must create** these secret **shells** on `apply` (empty JSON is fine). It does not put passwords or Stripe values in `.tf`. **`sync-secrets` must then write every field in the table** (GitHub Environment values + RDS hostname/port/db name + JDBC/URI strings it **builds**). App CD **fails** if the shell is missing or a required field is empty (`describe-secret` / compose `get-secret-value`). Infra `apply` is not done until those parameters exist.

#### Postgres fields (required in `heavy-rental/rest` and `heavy-rental/haystack`)

`sync-secrets` must write **each** of these, not only a single URL:

| JSON field | Source | Example |
| --- | --- | --- |
| `POSTGRES_HOST` | Terraform RDS endpoint hostname | `heavy-rental.xxxx.us-east-1.rds.amazonaws.com` |
| `POSTGRES_PORT` | Terraform (default `5432`) | `5432` |
| `POSTGRES_DATABASE` | Convention / Ansible | `heavy_rental` (REST) or Haystack db name |
| `POSTGRES_USERNAME` | GitHub Environment | `heavy_rental` |
| `POSTGRES_PASSWORD` | GitHub Environment `SPRING_DATASOURCE_PASSWORD` (or Haystack equivalent) | *(never log)* |
| `POSTGRES_URL` | Built by Actions | REST: `jdbc:postgresql://<host>:<port>/<database>`. Haystack: `postgresql://<user>:<password>@<host>:<port>/<database>` |

Spring Boot also maps `SPRING_DATASOURCE_URL` = `POSTGRES_URL`, `SPRING_DATASOURCE_USERNAME` / `_PASSWORD` = the same user/password. Fail `sync-secrets` if host, database, password, or port is empty.

#### Stripe (portal + REST only)

| Field | `heavy-rental/portal` | `heavy-rental/rest` | Source |
| --- | --- | --- | --- |
| `STRIPE_PUBLISHABLE_KEY` | **Yes** (`pk_…`) | **Yes** | GitHub Environment |
| `STRIPE_SECRET_KEY` | **No** | **Yes** (`sk_…`) | GitHub Environment |
| `STRIPE_WEBHOOK_SECRET` | **No** | **Yes** (`whsec_…`) | GitHub Environment |

The React portal is a browser app: it may use the **publishable** key only. Charges, webhooks, and the secret key stay on the Spring REST API (private subnet). Do not bake `sk_` into the Vite image. `sync-secrets` fails if REST is missing `STRIPE_SECRET_KEY` when Stripe is in use.

#### SSH private keys (one per ASG — **after** EC2 is InService)

Everyday shell is **SSM Session Manager**. The private PEM is break-glass only.

**The PEM is written to Secrets Manager only after Terraform has created the ASGs and the instances are `InService`.** Do not generate, log, or `put-secret-value` a private key during `plan`, during apply, or when desired capacity is 0.

| When | What |
| --- | --- |
| Terraform apply | Launch templates + ASGs + **empty** `heavy-rental/ssh/*` secret shells. **No PEM.** Preferred: **no** `key_name` on the launch template (SSM does not need one). |
| Wait | ASG instances reach **InService** (and SSM is reachable). |
| Job `sync-ssh-keys` | `ssh-keygen` (or GitHub Environment key material) → `put-secret-value` PEM → SSM installs the **public** key into `~/.ssh/authorized_keys`. |
| Configurer later | `get-secret-value` `heavy-rental/ssh/rest` → PEM file mode 600 → SSM port-forward to `:22`. |

| Secrets Manager id | Key name (Academy) | Who retrieves |
| --- | --- | --- |
| `heavy-rental/ssh/portal` | `hr-academy-portal` | Configurer / Actions — **not** the instance |
| `heavy-rental/ssh/rest` | `hr-academy-rest` | same |
| `heavy-rental/ssh/haystack` | `hr-academy-haystack` | same |
| `heavy-rental/ssh/neo4j` | `hr-academy-neo4j` | same |

```json
{
  "key_name": "hr-academy-rest",
  "private_key_pem": "-----BEGIN OPENSSH PRIVATE KEY-----\n..."
}
```

Never `tls_private_key` in Terraform (that puts the PEM in state). Allowed alternative: Terraform `aws_key_pair` from the **public** key only so first boot already has it — the **private** PEM still waits for InService + `sync-ssh-keys`. RDS has no SSH OS — no `heavy-rental/ssh/rds`. `configure-only` may refresh PEMs only if instances already exist.

Do **not** design around Vocareum `vockey`. Do **not** open `:22` from `0.0.0.0/0`. Optional: `:22` from a management SG only. Connect with **SSM port-forward to :22**, then `ssh -i rest.pem ec2-user@127.0.0.1`.

#### Retrieve

On the instance (app / Postgres / Stripe — Ansible via SSM):

```bash
aws secretsmanager get-secret-value \
  --secret-id heavy-rental/rest \
  --query SecretString --output text > /run/heavy-rental/rest.json
# map JSON → .env; chmod 600; docker compose up
```

Configurer retrieving an SSH PEM (break-glass; `set +x`; never print the PEM):

```bash
aws secretsmanager get-secret-value \
  --secret-id heavy-rental/ssh/rest \
  --query SecretString --output text \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["private_key_pem"])' \
  > /run/heavy-rental/rest.pem
chmod 600 /run/heavy-rental/rest.pem
```

Attach **`LabInstanceProfile`** (`LabRole`). Actions / Vocareum user: `PutSecretValue` on the app and SSH ARNs.

**Academy cannot enforce per-ASG `GetSecretValue`.** Every instance shares `LabRole`. If that role can read `heavy-rental/rest`, the portal host can too. Treat isolation as **convention**: Ansible writes only that role’s JSON to `.env`; do not fetch `sk_` or PEMs onto `asg-portal`. **Paid** must use **separate instance profiles** so portal cannot read `heavy-rental/rest` or `heavy-rental/ssh/*`. Configurer / Vocareum user: `GetSecretValue` on `heavy-rental/ssh/*`.

`configure-only` still runs **sync-secrets** then **`sync-ssh-keys`** (only if instances are InService) then Ansible so a password, Stripe, or SSH-key change lands in AWS without a full apply.

#### GitHub Environment inventory (not one list for every project)

GitHub Environments are **per repository**. They are **not** defined the same way from every pipeline tree. The maintainer **copies** Environment **`academy`** / **`paid`** onto the **CD** repo (same secret **names**). CI families use **other** Environment names and often **other** keys. CI does **not** all read `academy`/`paid`.

| Project | GitHub Environment | Secrets / variables | Notes |
| --- | --- | --- | --- |
| REST Integration CI | **`integration`** | Secrets: `REST_API_DB_NAME`, `REST_API_DB_USER`, `REST_API_DB_PASSWORD`, `REST_API_DB_PORT` | QC only. Caller must not set `environment:` on `uses:` |
| REST Release CI | **`production`** | Secrets: `REST_API_CLOUD_DB_HOST`, `REST_API_CLOUD_DB_NAME`, `REST_API_CLOUD_DB_USER`, `REST_API_CLOUD_DB_PASSWORD`, `REST_API_CLOUD_DB_PORT` | **Different names** than CD `SPRING_DATASOURCE_*` / `POSTGRES_*` |
| Haystack CI (Fast Feedback, Integration, Release) | **None** | No DB / Neo4j / LLM secrets | Workflows **fail** if `LLM_API_KEY` is set |
| Portal CI | **None** for app config | `GITHUB_TOKEN` for GHCR | No Stripe in CI |
| Mobile CI | **None** for AWS | APK only | Not deployed to the VPC |
| **Infra CD Academy** (this study) | **`academy`** | Secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `SPRING_DATASOURCE_PASSWORD`, `NEO4J_PASSWORD`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`. Variable: `AWS_REGION` | Vocareum keys for the **runner** only. App passwords feed `sync-secrets`. Example: `aws-infra-pipeline.example.yml` |
| **Infra CD Paid** | **`paid`** | Variables: `AWS_ROLE_TO_ASSUME`, `AWS_REGION`. Same **app** secrets as academy (Postgres password, Neo4j, Stripe). **No** Vocareum access keys | OIDC only |
| **Portal / REST / Haystack app CD (Academy)** | **`academy`** (same **names** as infra; copy onto each app-CD repo) | Secrets (fallback): **`AWS_ACCESS_KEY_ID`**, **`AWS_SECRET_ACCESS_KEY`**, **`AWS_SESSION_TOKEN`**. Variable: `AWS_REGION`. Optional `IMAGE_HTTP_URL` | **Vocareum only.** Runner may paste the three keys on Run workflow (they change every Start Lab) or use Environment fallback. Never on paid. Never in SM / on EC2 |
| **Portal / REST / Haystack app CD (Paid)** | **`paid`** | Variables: `AWS_ROLE_TO_ASSUME`, `AWS_REGION`. Optional `IMAGE_HTTP_URL`. **No** `AWS_ACCESS_KEY_ID` | OIDC only. Paid YAML **fails** if an access key is set |

**Name mismatch:** REST CI `REST_API_CLOUD_DB_*` is **not** automatically the same as CD `SPRING_DATASOURCE_PASSWORD` or Secrets Manager `POSTGRES_*`. `sync-secrets` **builds** host/port/database/URL from Terraform + the CD Environment password. Do not assume one GitHub secret feeds both CI QC and AWS RDS.

Study-only (MD, not Haystack CI YAML): `LLM_API_KEY` may land in `heavy-rental/haystack` at **runtime** if the class uses an LLM. Haystack **CI** must still leave it unset.

### 6.0b HTTPS on the public ALB (Academy)

**Default: HTTP :80.** You cannot mint a trusted public cert for the raw ALB DNS name (`*.elb.amazonaws.com`). Do not block the class on HTTPS.

Vocareum lists **AWS Certificate Manager (ACM)**. If the class **already owns** a domain:

1. Request an ACM public certificate in `us-east-1` for that name.
2. Validate with **DNS at the registrar** (CNAME) or email. You **cannot register** a domain in the lab.
3. Terraform: HTTPS `:443` listener + optional `:80` → `:443` redirect.
4. Target group stays **HTTP :80** to nginx.

Internal REST/Haystack ALBs stay HTTP inside the VPC. Do **not** enable HTTPS on them (private CA / ACM PCA cost; does not change the “not public” rule).

### 6.1 Component → AWS service

| Component | AWS service (Academy) | Notes |
| --- | --- | --- |
| `heavy-rental-network` | **VPC** + subnets + security groups | All resources in this VPC. |
| Public ingress | **Internet-facing ALB inside the VPC** (public subnets + IGW) | **Portal only** (`tg-portal` instance :80). HTTP :80 always. HTTPS :443 when an ACM cert exists. No REST, no Haystack. |
| REST ingress | **Dedicated internal ALB** | `scheme=internal`, `tg-rest` :8080, health `GET /actuator/health` or `/` |
| Haystack ingress | **Dedicated internal ALB** | `scheme=internal`, `tg-haystack` :8000, health `GET /docs` or `/health` |
| Portal / REST / Haystack compute | **One ASG each** in the **private app** subnets (launch template + `LabInstanceProfile`) | Never a lone EC2. Images from ECR or GHCR tar. |
| Neo4j compute | **`asg-neo4j`** in the **private data** subnets (launch template + `LabInstanceProfile`) | `neo4j:5` container. No Marketplace AMI. `max=1`. |
| `postgres-primary` | **RDS PostgreSQL** in the **data subnet group only** | `publicly_accessible = false`. SG: `sg-rest` + `sg-haystack` only. Engine Postgres. Size micro/small. `multi_az = false`. |
| `postgres-haystack` + pgvector | **Same one RDS, second database** *or* Postgres+pgvector **container on `asg-haystack`** | Two RDS instances will burn the budget. Confirm `CREATE EXTENSION vector`; if blocked, run `pgvector/pgvector:pg17` on the **app** ASG. |
| `postgres-haystack-sync` | Container on **`asg-haystack`** | `SOURCE_HOST` = RDS endpoint (data subnet); `TARGET_HOST` = Haystack DB. |
| Neo4j | Container on **`asg-neo4j`** (`neo4j:5`) | Bolt `7687` from `sg-haystack` only. Do not publish 7474/7687 to the internet. |
| `neo4j-populate` | Container on **`asg-haystack`** | Worker, not the database. Talks Bolt to `asg-neo4j` and SQL to RDS. Trigger URL stays internal (`http://neo4j-populate:8089` on the Haystack host). |
| Image registry | **ECR** in us-east-1 | Copy from GHCR during a lab session, or `docker load` the release tar. Push `neo4j:5` to ECR so `asg-neo4j` does not pull Docker Hub through a NAT Gateway. |
| App / Postgres / Stripe / SSH PEMs | **AWS Secrets Manager** | App JSON `heavy-rental/{portal,rest,haystack,neo4j}` (Postgres host/port/db/user/password/URL; Stripe on portal+REST). SSH PEMs `heavy-rental/ssh/{portal,rest,haystack,neo4j}`. Instances `get-secret-value` app JSON; configurer retrieves PEMs. |
| Logs | **CloudWatch** agent or `docker logs` on EC2 | Keep it small. |
| Bastion / SSH | **SSM Session Manager** via `LabRole` (everyday). SSH PEM from Secrets Manager (break-glass). | No `:22` from the internet. |
| Stable public URL | Public **portal** ALB DNS | Instance IPs change on scale/replace; clients use ALB DNS only. |

### 6.2 VPC layout

- **Region:** `us-east-1` (vockey key pair exists there).
- **One VPC** holds **all** of: public ALB, both internal ALBs, **`asg-portal`**, `asg-rest`, `asg-haystack`, **`asg-neo4j`**, and RDS. Nothing except the client browser is outside the VPC.
- **Three subnet tiers (example CIDRs — Terraform in the other project owns the real values):**

| Tier | Example CIDRs | Route | Contents |
| --- | --- | --- | --- |
| Public (2 AZs) | `10.0.0.0/24`, `10.0.1.0/24` | `0.0.0.0/0` → IGW | Internet-facing **portal ALB only** + IGW. Optional NAT instance ENI lives here. |
| Private **app** (2 AZs) | `10.0.10.0/24`, `10.0.11.0/24` | `0.0.0.0/0` → NAT instance (not NAT Gateway) | `asg-portal`, `asg-rest`, `asg-haystack`, both internal ALBs |
| Private **data** (2 AZs) | `10.0.20.0/24`, `10.0.21.0/24` | No IGW. No public IPs. `map_public_ip_on_launch = false`. Outbound (Neo4j image pull / SSM) via the **same** NAT instance, or VPC endpoints | **RDS subnet group** + **`asg-neo4j` only** |

- **Placement (read this twice):** the data subnet **group** lists **both** AZs because AWS requires two subnets for RDS. That is **not** Multi-AZ and **not** “one RDS per AZ” or “one Neo4j per AZ.” Academy runs **one** RDS (`multi_az = false`) and **one** `asg-neo4j` (`max=1`). Each process sits in **one** of the two data subnets. The other subnet is empty capacity.
- **RDS subnet group** lists **only** the two data subnets. `publicly_accessible = false`.
- **Portal instances** do **not** need a public IP; the public ALB targets them inside the VPC.
- **Outbound for private ASGs (image pulls):** **Do not use NAT Gateway** on a $50 lab. Prefer a **NAT instance** `t3.nano` shared by the app **and** data private route tables. If credits force it, `asg-portal` may use public subnets **still inside the VPC**, SG 80 only from `sg-alb-public`. REST / Haystack / Neo4j / RDS stay private with **no public IPs**.
- **Security groups:**
  - `sg-alb-public`: 80 (and 443 if used) from the internet
  - `sg-alb-rest`: 8080 from `sg-portal` only (and from `sg-alb-rest` health)
  - `sg-alb-haystack`: 8000 from `sg-rest` only
  - `sg-portal`: 80 from `sg-alb-public`
  - `sg-rest`: 8080 from `sg-alb-rest`; egress `5432` to `sg-rds` **and `8000` to `sg-alb-haystack`** (Tomcat → `HAYSTACK_URL`). No egress `7687` (REST does not talk Bolt)
  - `sg-haystack`: 8000 from `sg-alb-haystack`; egress `5432` to `sg-rds` and `7687` to `sg-neo4j`; `8089` stays on the Haystack instance SG for the populate worker
  - `sg-rds`: **5432 from `sg-rest` and `sg-haystack` only** — not from `sg-portal`, `sg-alb-public`, `sg-neo4j`, or `0.0.0.0/0`
  - `sg-neo4j`: **7687 from `sg-haystack` only**; optional `7474` from `sg-haystack` for SSM-forwarded Browser
  - Optional `:22` on each instance SG **only** from a management SG (for PEM break-glass). **Never** `:22` from `0.0.0.0/0`
  - No public 8080, 8000, 5432, 7474, 7687, or 8089

### 6.2a Data tier — why this still works on AWS Academy

The data-subnet split uses only allow-listed building blocks. It does **not** need paid-only features.

| Concern | Academy answer |
| --- | --- |
| Extra subnets / route tables | Ordinary VPC. Vocareum allows VPC. |
| RDS in a private subnet | Yes. `aws_db_subnet_group` on the two data subnets. `publicly_accessible = false`. `multi_az = false`. Class ≤ `medium`. Storage ≤ 100 GB gp2. No enhanced monitoring. |
| Two AZs for a single-AZ RDS | **Required by AWS** for a subnet group, even when Multi-AZ is forbidden. Two data subnets, one RDS instance. |
| Neo4j with no Marketplace AMI | `neo4j:5` **container** on Amazon Linux in `asg-neo4j`. Attach `LabInstanceProfile`. Do **not** create an IAM role. |
| Fourth ASG / instance count | Desired 1+1+1+1 = **4**, or **5** with a NAT instance. Cap is **9** instances / **32** vCPU / class ≤ **large**. Stay at desired=1. |
| Neo4j memory | `asg-neo4j` = `t3.large` (allowed). `asg-haystack` can drop to `t3.small` once the graph process leaves it. Cap Neo4j heap 512m–1G as in compose. |
| Image pull without NAT Gateway | Copy `neo4j:5` to **ECR** as the Vocareum user (LabRole is pull-only). `asg-neo4j` pulls via the **NAT instance** or **ECR + S3 VPC endpoints**. Never a NAT Gateway. |
| SSM onto a data-subnet host | Same as Haystack: `LabInstanceProfile` + NAT instance **or** interface endpoints `ssm` / `ssmmessages` / `ec2messages`. No SSH :22. |
| Secrets Manager from data subnet | `LabRole` can `GetSecretValue`. If there is no NAT, add a `secretsmanager` interface endpoint — or keep the shared NAT instance. |
| Stateful Neo4j + ASG | `max=1`, EC2 health only, scale-in protection, EBS for `/data`. Graph is rebuildable from RDS via `neo4j-populate`. Do not invent Multi-AZ Neo4j on the lab. |
| Session end vs credits | Vocareum **stops EC2** (including `asg-neo4j` and the NAT instance). **RDS and ALBs may keep billing.** See **§3.1**. `action=stop` must call `aws rds stop-db-instance`. Intact ≠ free. |
| What Academy must **not** add for this split | NAT Gateway, a second RDS, Multi-AZ, Marketplace Neo4j AMI, a new IAM role, an internet-facing Neo4j/RDS address, EKS. |

If lab credits cannot afford the fourth instance, the **documented fallback** is to keep Neo4j as a container on `asg-haystack` **and still put RDS in the data subnet group**. That fallback is worse isolation (graph shares the app host) and is **not** the default. Do not put RDS in the app subnets to save money — the extra data subnets themselves are free.

### 6.2b Neo4j Marketplace listing — evaluated and rejected for Academy

Listing evaluated: [Neo4j Community Edition](https://aws.amazon.com/marketplace/pp/prodview-a5jr6bo72f5aw) (`prodview-a5jr6bo72f5aw`). Delivery is a **CloudFormation** stack (“Single Instance”, template 2026.03.05, Neo4j 2026.01.3 on Amazon Linux 2023), not “pick an AMI and drop it in our data subnet.”

**Do not use this listing on AWS Academy.** Vocareum: Marketplace AMIs **not supported**. The vendor template would also break the lab even if Marketplace were allowed.

| What the vendor stack creates | Why it fails this study |
| --- | --- |
| Its **own VPC** + public subnet + IGW | Neo4j must live in **our** private data subnets next to RDS, not a second VPC |
| Public **NLB** on **7474 and 7687** + **Elastic IP** | Bolt/Browser must not be internet-facing |
| **IAM instance role** | Academy cannot create IAM roles. Only `LabRole` / `LabInstanceProfile` |
| CloudFormation apply | CD is Terraform. Do not mix CFN/CDK with Terraform on the same estate |
| Instance types include `r8i.*` and `t3.xlarge` | Academy class cap is **≤ large** (`t3.large` max) |
| SG from a configurable CIDR | Easy to open 7474/7687 to `0.0.0.0/0` |

Software is ~$0.04/hour plus EC2. Community Edition has no separate license fee; it is still a Marketplace product.

| Destination | Decision |
| --- | --- |
| **Academy (this section)** | **Rejected.** Use `neo4j:5` on `asg-neo4j` in the data subnets. |
| **Paid** | Out of scope here. See **§6P** — vendor CFT still rejected; Marketplace AMI inside *our* data-subnet ASG is optional only. |

### 6.3 Why not two RDS instances?

Compose isolates `postgres-primary` and `postgres-haystack`. In a commercial account that maps to two RDS instances. On Academy:

- Two `db.t3.small` instances left running will dominate the credit budget.
- Multi-AZ is forbidden anyway.

**Recommendation:** one RDS for REST; run Haystack pgvector as a container **on `asg-haystack`**.

That is **not** “an RDS instance that belongs to `asg-rest` only.” Academy has **one** RDS. `asg-rest` uses database `heavy_rental` (SoR). `sg-rds` still allows **`sg-haystack` :5432** because `postgres-haystack-sync` and `neo4j-populate` must **read** that same instance. Portal never reaches `:5432`. REST never reaches Bolt. Paid may add a **second** RDS for Haystack pgvector; REST still uses its own instance on `:5432`.

### 6.4 Instance sizing (stay on allow-list)

| Workload | Suggested | Academy notes |
| --- | --- | --- |
| `asg-portal` | `t3.micro` or `small` | App subnet |
| `asg-rest` | `t3.small` | App subnet |
| `asg-haystack` (Haystack + workers, **no** Neo4j) | `t3.small` or `medium` | App subnet. No longer sized for graph heap. |
| `asg-neo4j` (`neo4j:5` only) | **`t3.large`** (memory) | **Data** subnet. `max=1`. Heap 512m–1G. |
| NAT instance (optional) | `t3.nano` | Public subnet. Shared by app + data private routes. **Not** a NAT Gateway. |
| RDS | `db.t3.micro` or `small`, 20 GB gp2 | **Data** subnet group. `multi_az = false`. |

Hard caps: class ≤ **large**, ≤ **9** instances **across all ASGs + NAT**, ≤ **32** vCPU. Desired 1+1+1+1 (and one nano NAT) stays inside that.

Stop ASGs (desired=0 or instance stop via `action=stop`) — including **`asg-neo4j`** — and RDS when the lab day ends. **Ending the Vocareum session does not freeze the budget** (§3.1). RDS left running is the usual credit leak. RDS left stopped for seven days is **auto-started by AWS** and will spend credits again.

### 6.4a Container resource limits (Ansible compose)

When the compose playbook starts containers, it **must** set `mem_limit` / `cpus` (Compose v2 `deploy.resources.limits` is fine if the engine honors them; otherwise classic `mem_limit` + `cpus`). Leave **256–512 MiB** on the host for Amazon Linux, SSM, and Docker. `restart: unless-stopped`. **No** `replicas > 1` on one EC2. **Do not** start Neo4j on `asg-haystack`.

| ASG | Host RAM (approx) | Container | `mem_limit` | `cpus` | Notes |
| --- | --- | --- | --- | --- | --- |
| `asg-portal` | `t3.micro` ~1 GiB | nginx | `256m` | `0.5` | One portal image |
| `asg-rest` | `t3.small` ~2 GiB | Tomcat | `1g` | `1.0` | Heap inside this cap |
| `asg-haystack` | `t3.small` ~2 GiB | uvicorn (CI image) | `768m` | `1.0` | Haystack app CD must keep this |
| | | postgres-haystack-sync | `256m` | `0.25` | Worker |
| | | neo4j-populate | `256m` | `0.25` | Worker |
| | `t3.medium` ~4 GiB if pgvector | optional pgvector | `512m` | `0.5` | Do **not** fit pgvector on `t3.small` |
| `asg-neo4j` | `t3.large` ~8 GiB | `neo4j:5` | `4g` | `1.5` | `NEO4J_HEAP_INITIAL_SIZE` / `MAX` **512m–1G**; pagecache ≤ 2g |

Haystack **app CD** re-runs compose on `asg-haystack` with the **same** haystack-row limits when it loads a new CI image. Portal **app CD** re-runs compose on `asg-portal` with the **same** nginx-row limits (`256m` / `0.5`) and must keep the `/api` → `REST_BASE_URL` proxy.

### 6.5 What Academy must not build

- NAT Gateway
- Multi-AZ RDS, a second RDS, or a Neo4j replica in the other AZ
- Marketplace Neo4j / the vendor CloudFormation stack (`prodview-a5jr6bo72f5aw`)
- A new IAM role or OIDC provider (use `LabRole` / `LabInstanceProfile` only)
- Public 8080, 8000, 5432, 7474, 7687, 8089, or **22**
- `STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET` on the portal secret or in the Vite image
- SSH PEMs or Postgres passwords in `.tf`, git, or the job summary
- RDS or `asg-neo4j` in public or app subnets
- EKS / Fargate as the default
- CDK apply mixed with Terraform on this VPC

### 6.6 System design principles

These apply to the **current** design (§6 Academy, §6P paid). They do **not** change the topology. Academy **does not** claim Multi-AZ data, CPU autoscaling, or strong consistency on Neo4j.

#### Fault tolerance

**Academy:** Public and internal ALBs. ELB health checks **replace** an unhealthy portal / REST / Haystack node. Subnets span **two AZs** so a replacement can land in the other AZ. Neo4j is **derived state** — if `asg-neo4j` is replaced, `neo4j-populate` rebuilds the graph from RDS. After a Vocareum restart, `configure-only` brings containers back.

**Limit:** **One** RDS (`multi_az = false`) and **one** Neo4j (`max=1`). Losing that AZ takes the data tier offline. Two data subnets are **not** two databases.

**Paid:** Optional Multi-AZ RDS (primary + **standby**, still one writer). App ASGs may run `desired > 1`. Neo4j stays `max=1`.

#### Maintainability

**Academy:** Terraform owns VPC/ASG/ALB/RDS; Ansible owns Docker, `.env`, and RDS *logical* state (idempotent). `configure-only` updates images/secrets without recreating RDS. Secrets live in Secrets Manager, not `.tf`. CI builds the image; CD deploys it. Operators use SSM (PEM only after InService, break-glass). Academy and paid are **two workflows / two states**.

**Limit:** Vocareum tokens expire; lab **reset** wipes S3 state — re-apply from Git.

**Paid:** OIDC + Environment reviewers. Optional second RDS still in the **same** data subnet group.

#### Scalability

**Academy:** One ASG per role so a single tier *can* grow (`max=2` on portal/REST/Haystack).

**Limit:** Scale **policies stay off** (credits). Caps: ≤ **9** instances, class ≤ **large**. RDS and Neo4j do **not** scale out.

**Paid:** Target-tracking on **app** ASGs only; larger instance classes; optional second RDS for Haystack pgvector.

#### Reliability

**Academy:** ELB + compose `restart: unless-stopped`. Clients use **ALB DNS**, not instance IPs. `assert-lab` before apply. `action=stop` so idle RDS/EC2 do not exhaust the budget and wipe the account (§3.1). CloudWatch on ALB 5xx, unhealthy targets, RDS CPU. Credentials from Secrets Manager.

**Limit:** Single-AZ RDS/Neo4j. Session end **does not** freeze credits.

**Paid:** Multi-AZ RDS, HTTPS on the public portal ALB, NAT Gateway or VPC endpoints.

#### Consistency

**Academy:** **RDS PostgreSQL is the system of record** (one writer, ACID). Neo4j is **derived** (SQL → Cypher). Haystack sync **polls** (~60s) — **eventual**, not CDC, not DMS. `sync-secrets` is the only write path into Secrets Manager.

**Limit:** Graph and search can **lag** RDS. Not multi-master. Do not treat Neo4j as SoR.

**Paid:** Same model. A second RDS is still one writer per database.

#### Communication

**Runtime (Academy and paid):**

```
Browser  →  public portal ALB :80/:443
              →  asg-portal  (nginx SPA + /api proxy)
                    →  internal REST ALB :8080
                          →  asg-rest
                                →  RDS :5432          (SoR database heavy_rental)
                                →  internal Haystack ALB :8000   (HAYSTACK_URL)
                                      →  asg-haystack
                                            →  RDS :5432          (sync/populate; optional Haystack db)
                                            →  Neo4j Bolt :7687   (asg-neo4j; sg-haystack only)
```

Security groups **are** the contract. Browser / mobile never call REST, Haystack, RDS, or Bolt. Operators: SSM (or SSM port-forward + PEM). CD: Actions → Terraform outputs → Secrets Manager → instance `get-secret-value`.

**Paid extras:** HTTPS at the **portal** edge only; optional **internal** Bolt NLB. Still no public API.

### 6.7 System design trade-offs

System design is a set of **trade-offs**. Cost, scalability, reliability, maintainability, robustness, performance, security, and usability cannot all be maximized on a Vocareum credit budget. Theoretical pairs — **time vs space**, **latency vs throughput**, **performance vs scalability**, **consistency vs availability (CAP / PACELC)** — show up in this estate as well. This study balances them for a **class lab** first, then a **paid** account with the same communication graph.

§6.6 is what we **keep**. This section is what we **gave up**, and why.

A highly reliable, highly scalable estate (Multi-AZ RDS, CPU scale-out, HA Neo4j) needs more expensive components. On Academy those components either **violate the allow-list** or **consume the budget** until the account is disabled. If cost is the constraint, we sacrifice some robustness and scale — we do **not** sacrifice private APIs or the data-subnet split.

#### Cost versus reliability, robustness, and scalability

| We chose (Academy) | We gave up | Why |
| --- | --- | --- |
| One single-AZ RDS; Neo4j `max=1`; scale policies **off**; NAT **instance** not Gateway | Multi-AZ, HA graph, CPU scale-out | Credits + Vocareum caps (class ≤ large, ≤ 9 instances, no Multi-AZ) |
| Three ALBs (public portal + internal REST + internal Haystack) | One cheaper shared ALB | REST/Haystack must not share the public listener |
| Four ASGs vs one public EC2 + Compose (option D) | Fewer instances / lower idle cost | Replace and isolate by role; no lone EC2 |
| `action=stop` for the lab day; `action=destroy` only to wipe the estate | Daily `terraform destroy` | Keep ALB DNS and RDS data across sessions. Idle ALBs/EBS still bill until **destroy** (§3.1, §7.2d) |

**Paid** may buy the left-behind side (Multi-AZ standby, NAT Gateway, app `desired > 1`) **without** changing who may talk to whom.

#### Time versus space

Time–space (time–memory) trade-offs show up in algorithms and in this **distributed** estate: extra memory or storage avoids repeating expensive work so more requests are **lookups** of precomputed values.

| Space we keep | Time we save | Cost of that space |
| --- | --- | --- |
| **Neo4j** on `asg-neo4j` | Graph walks without heavy SQL joins on every request | Extra `t3.large` + EBS; rebuild with `neo4j-populate` |
| **Haystack / pgvector** (second DB or container) | Embedding **lookup** instead of re-embed on every query | Memory/disk; sync **polls** ~60s |
| **ECR in-region** copy of release images + `neo4j:5` | Faster pull than GHCR / Docker Hub after each Start Lab | ECR storage |
| Secrets Manager JSON (host, port, JDBC, Stripe, ALB DNS) | Instances do not re-derive connection strings | Small SM cost |

We do **not** precompute everything. Haystack sync is poll, not CDC: simpler pipeline, **stale by ~60s**. That is **time-lag versus complexity**, not extra RAM. RDS stays the system of record; Neo4j and Haystack are **lookup tables** derived from it.

#### Latency versus throughput

**Latency** is how long a request waits to be handled. **Processing time** is work after pickup. **Response time** = latency + processing time (plus network).

**Bandwidth** is the theoretical max data rate between two points. **Throughput** is how much is actually transmitted and processed. Throughput is always ≤ bandwidth unless the path is fully used. Devices have finite capacity; too little bandwidth causes **congestion**. High latency queues packets, which **lowers** throughput — the two move inversely under load.

Measure latency with **percentiles** (p50, p90, p99), not the average (outliers warp the mean). p90 is the slowest of the fastest 90% of requests. Design for **maximal throughput inside an acceptable latency**.

| Choice in this design | Effect on latency | Effect on throughput |
| --- | --- | --- |
| Browser → portal ALB → portal → **internal REST ALB** → REST → RDS / Haystack / Neo4j | Extra hops vs one public box | Isolation + health replace. ALB can spread load **only if** `desired > 1` |
| Academy `desired=1`, scale policies **off** | Fine for a class demo | **Capped.** More load raises p99; we do **not** add instances |
| Neo4j + pgvector (space, above) | Lower **processing time** for graph/search | Same host still saturates under a flood |
| Haystack poll ~60s | Not request latency; **freshness** lag | Avoids CDC load on RDS |
| ECR in-region | Faster **cold start** (image pull) | Not request throughput |
| One RDS writer + one Neo4j | Simple path | Single JDBC + single Bolt — **ceiling** under load |

**Academy target:** acceptable **demo** response time at **low** throughput. Do not tune the lab for high QPS.

**Paid:** raise throughput with app `desired > 1` / target-tracking. Watch **p99 target-response-time** on the public and internal ALBs (CloudWatch — Monitor, not a new product). One RDS writer and one Neo4j remain the data-tier ceiling unless that tier changes.

#### Performance versus scalability

**Performance** is how fast the system answers **one** request (single-user / p50). **Scalability** is whether adding resources improves behavior **in proportion** under **more** load.

- A **performance** problem: slow even for one user (e.g. p50 = 100 ms at rest).
- A **scalability** problem: fast for a few users (p50 = 1 ms at 100 requests) but slow in a flood (p50 = 100 ms at 100k requests).

A service is scalable only if extra instances/CPU buy a matching gain. Faster graph lookups are **performance**. A second portal node is **scalability**.

| Piece | Performance (one request) | Scalability (more load) |
| --- | --- | --- |
| Neo4j + pgvector | Better single-request graph/search (less join / re-embed) | Same `t3.large` / one Bolt — **`max=1`**, does not scale out |
| Internal ALBs | Extra hop — slightly worse one-request time | Required to spread load **if** `desired > 1` |
| Academy `desired=1`, scale policies **off** | Tuned for a **demo** (one student) | **Not** scalable. More users raise p50/p99; we do not add instances |
| One RDS writer | Fine for class write rate | Throughput ceiling. Multi-AZ is **HA**, not more writers |
| Four ASGs | Isolation — not a faster single request | **Shape** to grow one tier later; caps ≤ 9 / class ≤ large |

**Academy:** optimize **single-path demo performance**, not proportional scale. A second portal instance would be scale; we leave it off to save credits.

**Paid:** the scale lever is app `desired > 1` / target-tracking. The data tier (one RDS writer, one Neo4j) still does not scale out. Single-request speed still comes from Neo4j/pgvector and in-region ECR, not from more instances.

#### Consistency versus availability

**Strong consistency** means every read sees the most recent write. **High availability** means the system still returns a **non-error** response. In a distributed system the network drops or delays packets (the fallacies of distributed computing), so **partitions** happen. That is the **CAP theorem** (Brewer): you cannot have consistency (C), availability (A), and partition tolerance (P) at the same time. Partition tolerance must be designed in (networks are not reliable). **When a partition is happening**, you choose **C or A**.

CAP is often misread as “abandon one of C, A, or P at all times.” The choice between consistency and availability is only **during** a partition. The rest of the time the finer rule is **PACELC**.

**PACELC:** if **P**artition → choose **A** or **C** (CAP). **E**lse (healthy path) → choose **L**atency or **C**onsistency. Large systems replicate to survive partitions; then a normal read is either a **slower consistent** read (quorum / hop to the writer) or a **faster stale** local read.

This lab is **not** a three-region multi-master. The distributed pieces are four ASGs, ALBs, one RDS, and one Neo4j across **two AZs**. CAP and PACELC still apply on those links. We do **not** claim CA (pretend the network never fails).

| Store / path | If partitioned or lagging | Choice |
| --- | --- | --- |
| **RDS** (system of record, one writer) | App AZ cannot reach the DB | **CP:** REST/Haystack return errors. No split-brain, no second writer. Academy `multi_az=false` — that AZ down = **unavailable**. |
| **Neo4j** (derived, §6.6) | Bolt down or `neo4j-populate` behind | **AP-ish for graph reads:** may be **stale** vs RDS. If the only node is down (`max=1`), the graph is unavailable. **Not** SoR. |
| **Haystack / pgvector** | Sync poll ~60s, or Haystack host down | **Eventual / AP-ish:** search can be stale. **Not** SoR. |
| Portal → REST → Haystack (internal ALBs) | A hop fails | **Fail closed** — 5xx / unhealthy target. Do not invent a write on RDS. |

**One line:** **RDS is CP; Neo4j and Haystack are eventual (AP-ish).** Same as §6.6 (SoR vs derived).

| PACELC mode | This estate |
| --- | --- |
| **P** (partition) | **RDS = C** (error if unreachable). **Neo4j / Haystack = A / eventual** (stale, or down if the only node is gone). |
| **E** (no partition) — RDS | **C over L:** one writer, no local replica. Clients pay the hop to that AZ for a consistent read. Academy forbids Multi-AZ / replicas, so there is **no** replica-lag trade on Postgres. |
| **E** (no partition) — Neo4j / Haystack | **L over C:** graph/search answer **without** waiting for the last SQL write. Sync/populate can be ~60s behind. That is the healthy-path ELC choice on **derived** stores. |
| Internal ALBs (healthy path) | Extra hop = **latency** for isolation, not a replica-consistency choice. |

**Academy:** prefer **consistency on RDS** and accept **unavailability** if that instance is unreachable. Graph/search may stay usable while **behind** RDS; they must not be treated as the latest write.

**Paid Multi-AZ RDS:** better **availability** of the **same** consistent writer (standby) under **P**. Not a second writable copy. ELC on RDS only appears if you later add a **read replica**. Neo4j stays `max=1`.

#### Other weighed pairs

| Pair | Choice |
| --- | --- |
| **Security vs usability** | Internal ALBs + SSM. Students do not open REST in a browser. A demo uses SSM port-forward, not `0.0.0.0/8080`. |
| **Performance vs maintainability** | Four ASGs + Terraform/Ansible instead of option D (one public box). More moving parts; clearer blast radius. |
| **Consistency vs freshness** | RDS is ACID SoR. Graph/search are **eventual** (§6.6). |
| **Long-lived VPC vs daily destroy** | Keep ALB DNS and RDS data across lab sessions. Accept idle ALB and EBS charges; run `action=stop` for RDS compute. **`action=destroy`** is the wipe (end of class / failed estate), not the daily path. |

**User need this balances:** a credit-capped Academy lab that still isolates apps from data and keeps APIs private. Paid is the same communication graph with more reliability and scale budget — not a different product.

### 6.8 AWS Well-Architected Framework (guideline)

Use the official [AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html) (publication date 6 November 2024) as a **guideline** for this estate. It is a **constructive conversation** about decisions — **not an audit** and not a dump of the whole whitepaper.

This section covers the Framework pages we treat as required reading for the other project: [Welcome](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html), [Definitions](https://docs.aws.amazon.com/wellarchitected/latest/framework/definitions.html), [On architecture](https://docs.aws.amazon.com/wellarchitected/latest/framework/on-architecture.html), [General design principles](https://docs.aws.amazon.com/wellarchitected/latest/framework/general-design-principles.html), [The pillars](https://docs.aws.amazon.com/wellarchitected/latest/framework/the-pillars-of-the-framework.html), [The review process](https://docs.aws.amazon.com/wellarchitected/latest/framework/the-review-process.html), [Further reading](https://docs.aws.amazon.com/wellarchitected/latest/framework/further-reading.html), and the Framework [glossary pointer](https://docs.aws.amazon.com/wellarchitected/latest/framework/glossary.html).

The Framework helps you design and operate **secure, reliable, efficient, cost-effective, and sustainable** workloads, and to measure them against those qualities. **Security and operational excellence are generally not traded off** against the other pillars. Business context *does* drive other trades — on Academy we trade **reliability vs cost** (single-AZ RDS). That is allowed by the Framework.

#### Definitions ([source](https://docs.aws.amazon.com/wellarchitected/latest/framework/definitions.html))

| Term | Meaning here |
| --- | --- |
| **Component** | Code, config, and AWS resources that meet one requirement (e.g. `asg-rest`, the RDS instance). |
| **Workload** | The Heavy Rental runtime: portal + REST + Haystack + Neo4j + RDS in one VPC. |
| **Architecture** | How those components talk (public portal ALB → internal ALBs → data tier). |
| **Milestone** | Design, first `apply`, go-live demo, daily `action=stop`, end-of-class `action=destroy`. |
| **Technology portfolio** | Academy lab **and** paid account — two workloads, not one. |
| **Level of effort** | High / medium / low as in the Framework (weeks–months / days–weeks / hours–days). |

#### On architecture ([source](https://docs.aws.amazon.com/wellarchitected/latest/framework/on-architecture.html))

AWS prefers **distributed** architecture ownership (every team can design) plus **practices** and **mechanisms** (automated checks) over a single overlay architecture board. “Good intentions never work, you need good mechanisms.” The Well-Architected Framework is the customer-facing form of that internal review.

For this study: the **other project** owns the Terraform/Ansible. This file is the shared **practice**. GitHub Actions (`assert-lab`, no IAM on Academy, no public REST) are the **mechanisms**. We work backward from the **class** (credit-capped, private APIs) then the **paid** customer.

#### General design principles ([source](https://docs.aws.amazon.com/wellarchitected/latest/framework/general-design-principles.html))

| Principle | This estate |
| --- | --- |
| **Stop guessing capacity** | Academy fixes `desired=1` and size classes to the allow-list — we do **not** guess a huge fleet. Paid may scale **app** ASGs from data (ALB p99). |
| **Test at production scale** | Academy **cannot** afford a second full copy. Use `configure-only` and Integration CI images. Paid may stand up a short-lived twin and tear it down. |
| **Automate with experimentation in mind** | Terraform + Ansible in Actions. `plan` before `apply`. Revert = Git + re-apply. |
| **Evolutionary architectures** | Same three tiers from Academy → paid. Add Multi-AZ / HTTPS / second RDS **without** changing who may talk to whom. |
| **Drive architectures using data** | CloudWatch ALB 5xx, unhealthy targets, RDS CPU, p99 if enabled. Budget UI / Cost Explorer. |
| **Improve through game days** | **Not** a class requirement. Optional later on paid. Session-end + `configure-only` is the cheap failure drill. |

#### The six pillars ([source](https://docs.aws.amazon.com/wellarchitected/latest/framework/the-pillars-of-the-framework.html))

| Pillar | Official meaning | Academy | Gap | Paid |
| --- | --- | --- | --- | --- |
| **Operational excellence** | Run the workload, see operations, improve process | Actions CD; Terraform + Ansible; `plan` / `apply` / `configure-only` / `stop` / `destroy`; SSM; `assert-lab` | Vocareum tokens; no game days | OIDC + Environment reviewers |
| **Security** | Protect data, systems, assets | Three subnet tiers; internal REST/Haystack; SGs; Secrets Manager (Postgres, Stripe, SSH PEMs after InService); `LabRole`; no public 5432/7687; no `sk_` on the portal | Session access keys (no OIDC); HTTP portal default | OIDC; HTTPS on portal ALB |
| **Reliability** | Work correctly when expected; operate the lifecycle | ASGs + ELB replace; ALB DNS; Neo4j rebuildable from RDS; `action=stop` so a budget wipe is less likely | Single-AZ RDS/Neo4j | Multi-AZ RDS standby |
| **Performance efficiency** | Right resources; stay efficient as demand and tech change | Neo4j/pgvector for graph/search; ECR in-region; `t3.*` per role | `desired=1`; no Graviton/Lambda experiments | Larger classes; app scale-out |
| **Cost optimization** | Business value at the lowest price | No NAT Gateway / EKS; one RDS; scale policies off; `action=stop`; §3.1 | Idle ALBs still bill; EBS while stopped | Cost Explorer; right-size |
| **Sustainability** | Less energy; max value from what you provision | Stop idle compute; small classes; no always-on EKS/NAT GW | ALBs 24/7 | Do not turn on Multi-AZ until needed |

#### The review process ([source](https://docs.aws.amazon.com/wellarchitected/latest/framework/the-review-process.html))

- **Blame-free**, lightweight (**hours, not days**), a **conversation not an audit**.
- Outcome: **actions** that improve the people using the workload (class + operators).
- The team that **builds** the architecture should review it **continuously** (update answers as Terraform evolves), not only in a formal meeting.
- Review at **milestones**: early design (avoid one-way doors), before first `apply` / demo, after big changes. Many decisions are **two-way doors** (instance size, desired count). **One-way doors** (public REST, Marketplace Neo4j CFT, mixing CDK+Terraform) need more inspection — this study already **rejects** those.
- After a review: a **prioritized issue list**. Update the study when you close an issue.
- Typical objections (“too busy”, “no time to act”, “secrets of our solution”): a review before a class demo finds missed risks; WAF questions do not require proprietary app logic.

Suggested lab review kit: this file, the VPC diagram in §6, Terraform plan output, open questions in §12.

The [AWS Well-Architected Tool](https://aws.amazon.com/wellarchitected-tool/) is optional on **paid** later. Do not require it on Academy.

#### Further reading ([source](https://docs.aws.amazon.com/wellarchitected/latest/framework/further-reading.html))

- [AWS Architecture Center](https://aws.amazon.com/architecture/)
- [AWS Cloud Compliance](https://aws.amazon.com/compliance/)
- [Well-Architected homepage](https://aws.amazon.com/architecture/well-architected/) · [Partner program](https://aws.amazon.com/architecture/well-architected/partners/) · [WA Tool](https://aws.amazon.com/wellarchitected-tool/)
- Pillar papers: [Operational excellence](https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/welcome.html) · [Security](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html) · [Reliability](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html) · [Performance efficiency](https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/welcome.html) · [Cost optimization](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html) · [Sustainability](https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/welcome.html)
- [The Amazon Builders' Library](https://aws.amazon.com/builders-library/)
- [Well-Architected Labs](https://www.wellarchitectedlabs.com/)

#### Glossary

The Framework [glossary page](https://docs.aws.amazon.com/wellarchitected/latest/framework/glossary.html) points at the [AWS Glossary](https://docs.aws.amazon.com/glossary/latest/reference/glos-chap.html). Terms we use from **Definitions** are in the table above. Other study terms: **SoR** = RDS; **derived store** = Neo4j / Haystack; **break-glass** = SSH PEM after InService; **`action=stop`** = pause; **`action=destroy`** = `terraform destroy` of that state (§7.2d).

### 6.9 System design guidelines

These guidelines are **virtues** for why the estate looks like this — not a claim of perfection. A designer should see the **hidden costs** and still get it **right enough**. Five apply here: **isolation**, **simplicity**, **performance**, **trade-offs**, and **use cases** (it always depends). A short **conclusion** closes the set.

#### Guideline of isolation: build it modularly

> Controlling complexity is the essence of computer programming. — Brian Kernighan

Break a complex system into **smaller modules** that run on their own and still form one workload. That is how compose’s single `heavy-rental-network` becomes this VPC.

| Module | Independent how | Interface |
| --- | --- | --- |
| `asg-portal` | Replace or scale the nginx image without touching REST | Public ALB in; internal REST ALB out |
| `asg-rest` | Own ASG + internal ALB | RDS `:5432`; Haystack ALB |
| `asg-haystack` | Workers stay here; **no** Neo4j sidecar | RDS; Bolt to `asg-neo4j` |
| `asg-neo4j` | Data-subnet module; `max=1` | Bolt from haystack only |
| RDS | Managed; not an ASG | `sg-rds` from rest/haystack only |
| Public vs internal ALBs | Portal is the only public module | No `/api` or `/haystack` on the public listener |
| Subnet tiers | Public / app / data | Route tables + security groups |
| CI vs CD; academy vs paid | Separate workflows and state | Images in; **no** shared VPC |
| Terraform vs Ansible | Infra vs guest | Outputs → Secrets Manager → compose |
| Secrets | One JSON per ASG; `sk_` not on the portal | `get-secret-value` for **that** role only |

How modularity serves the usual requirements:

| Requirement | Here |
| --- | --- |
| **Maintainability** | Replace one ASG or `configure-only` one image. |
| **Reusability** | Paid copies the same three tiers and ALB pattern. |
| **Scalability** | Grow **one** app ASG later (paid). Neo4j/RDS stay single. |
| **Reliability** | ELB replaces one module. A failed hop **fails closed** — not a rewrite of the VPC. |

**Hidden cost:** more modules mean more ALBs, instances, SGs, and secret ids. Interfaces (ALB DNS, Bolt URI, JDBC) **must** live in Secrets Manager so modules do not hard-code each other. Academy pays that cost up to the credit cap (four ASGs, three ALBs). Option D (one public EC2 + compose) is the anti-pattern: cheaper, not isolated.

This is **not** EKS microservices. It is **component-based** split at ASG / ALB / subnet / pipeline boundaries, with SGs as the contract.

#### Guideline of simplicity: keep it simple, silly

> Everything should be made as simple as possible, but no simpler. — attributed to Albert Einstein

KISS: do not add features or layers the class does not need. Isolation already costs four ASGs and three ALBs. Simplicity is why we **stop there**.

| KISS principle | This estate |
| --- | --- |
| **Core requirements** | One VPC; portal public; REST / Haystack / RDS / Neo4j private; CI images; stay inside Academy credits |
| **Minimize components** | **No** EKS, Fargate, CDK+Terraform, Marketplace Neo4j CFT, second RDS, NAT Gateway, Multi-AZ, CPU scale-out, or WA Tool on the lab. **`destroy` is a CD action**, not a daily job |
| **Avoid overengineering** | Neo4j = `neo4j:5` container, not an Enterprise cluster. Haystack sync = poll ~60s, not DMS/CDC. Everyday shell = SSM; PEM only after InService |
| **Easy to use** | Students use the **portal ALB** only. Operators use **Run workflow** + `action`. No public SSH |
| **Test and refine** | CI Integration / Release. CD `plan` then `apply`. `configure-only` after Start Lab |

**Tension with isolation:** four ASGs + three ALBs is **more** parts than option D (one public EC2 + compose). That is “**no simpler**.” One public box would be simpler and **wrong** (public APIs). We do not add a fifth compute style (ECS) on Academy.

**Hidden cost of too much simplicity:** option D, REST on the public ALB, or Neo4j as a Haystack sidecar. Those fail security and isolation. KISS is not “one instance.”

#### Guideline of performance: metrics don’t lie

> Performance problems cannot be solved only through the use of Zen meditation. — Jeffrey C. Mogul

**Measure, then build.** You cannot bluff performance or scalability. **Metrics** are quantitative (utilization, response time, error rate, trends). **Observability** is inferring health from **externally visible** outputs — ALB stats, CloudWatch, logs — without SSH into every box. Instrument as you create the estate (CD may *create* log groups; Operate **uses** them — §2.1).

| Signal | Where | Why |
| --- | --- | --- |
| ALB 5xx, unhealthy host count | Public portal ALB + internal REST/Haystack ALBs | Request failures vs a dead target |
| **p99** target-response-time (not the average) | Same ALBs | Latency under load (§6.7). p50-only hides the tail |
| RDS CPU, connections, `FreeStorageSpace` | The one writer | Data-tier ceiling |
| EC2 status / ASG **InService** | Four ASGs | Replace; `sync-ssh-keys` waits for this |
| CloudWatch Logs / `docker logs` | Instances | App faults |
| Learner Lab budget / Cost Explorer | Account | Credits — session end ≠ free (§3.1) |
| `assert-lab` / `sts get-caller-identity` | CD | Do not apply on a dead Vocareum session |

**Not on Academy:** X-Ray, Managed Prometheus/Grafana, OpenSearch, RDS **enhanced** monitoring (allow-list and cost).

Do not add a second portal instance because the demo “felt slow.” Check **p99 vs one-request slowness** (§6.7 performance vs scalability). If p50 is already bad with one user, that is **performance** (Neo4j heap, image pull, SQL) — not scale.

#### Guideline of trade-offs: there is no such thing as a free lunch

> Get it right. Neither abstraction nor simplicity is a substitute for getting it right. — Butler Lampson

**TINSTAAFL:** every decision spends something. Optimizing one quality costs another. There is **no** design that wins on cost, scale, reliability, maintainability, and performance at once. Academy **credits** make that bill visible. The full catalog is **§6.7**; this guideline is why that section exists.

| Lunch we took | What we paid |
| --- | --- |
| Isolated APIs (three ALBs, four ASGs) | Idle ALB hours, more instances |
| Single-AZ RDS / Neo4j `max=1` | Unavailability if that AZ or node is gone (CAP **P**) |
| `desired=1`, scale policies off | Throughput / scalability |
| Neo4j + pgvector (space) | Extra `t3.large` + EBS |
| Eventual graph/search (PACELC **L**) | Stale vs RDS (~60s) |
| `action=stop` on lab days (not daily `destroy`) | ALBs and EBS still bill until `action=destroy` |
| KISS (no EKS, no CDC) | Not an HA graph, not high QPS |
| Option D **rejected** | Not the cheapest single box |

A highly tuned one-off (Marketplace Neo4j CFT, EKS) would buy a narrow win and **lose** maintainability or the allow-list. A one-box compose stack is simpler and **wrong** for private APIs. **Right** here means class lab + private APIs + data-subnet split. Paid can **buy** another lunch (Multi-AZ, app scale-out) — that lunch is still not free.

#### Guideline of use cases: it always depends

> Not everything worth doing is worth doing well. — Tom West

There is **no silver bullet**. The same compose problem can be EKS, one public EC2, or a Marketplace Neo4j stack — “best” for someone else. Design **depends** on requirements, users, tech limits, cost, scale, maintenance, and (here) Vocareum rules. We pick something **reasonable** and **good enough** for the stated user — not perfect HA.

| Factor | What this study optimized for |
| --- | --- |
| **Users** | Students: **portal ALB** only. Operators: Actions + SSM |
| **Constraints** | Allow-list, ≤ 9 instances, no Multi-AZ, no new IAM, credit budget |
| **Feasible** | Terraform + Compose-on-EC2 — not EKS |
| **Sustainable** | Long-lived VPC; daily `action=stop`; `action=destroy` only to wipe |
| **Good enough** | Single-AZ RDS, `desired=1`, poll sync — **not** Multi-AZ + CDC |

**Academy** and **paid** are **two use cases** and one communication graph. Paid extras (HTTPS, Multi-AZ, app scale) are not required to “finish” the class design. West: doing the lab “as well as” a multi-region bank is **not** worth it on a $50–$100 budget.

Silver bullets we **refused**: EKS, the Neo4j Marketplace CFT, one public EC2 (option D).

#### Conclusion

System design is a **seesaw**. You find an equilibrium among cost, scale, reliability, maintainability, security, and usability — **effective and efficient enough**, not perfect. Concepts live in **§6.6**. Trade-offs (including CAP/PACELC and the fallacies of a failing network) live in **§6.7**. The AWS Well-Architected **guideline** is **§6.8**. The five virtues above are how we avoid the usual pitfalls.

The basic **building blocks** are already chosen in this study — they are not a later textbook chapter:

| Block | This estate |
| --- | --- |
| **Data store** | RDS is the system of record. Neo4j and Haystack/pgvector are **derived** lookup stores |
| **Cache** | **No** separate cache tier (KISS). Neo4j/pgvector are not ElastiCache |
| **Load balancing** | Public portal ALB; dedicated **internal** REST and Haystack ALBs |
| **Networking** | One VPC, three subnet tiers, security groups as the contract |
| **Orchestration** | GitHub Actions → Terraform → `sync-secrets` → `sync-ssh-keys` → Ansible |

Next for the **other project**: implement that CD path. Paid uses the **same** blocks with more budget (Multi-AZ, HTTPS, app scale) — not a different product.

Assumptions **not** to make on this VPC: **§6.10**.

### 6.10 Fallacies of distributed computing

This workload is **distributed** (browser, ALBs, four ASGs, RDS, Neo4j, GitHub Actions). L. Peter Deutsch’s **eight fallacies** are false assumptions that lead to bad implementations. We **reject** them here. Trade-offs after you reject them are **§6.7**. Well-Architected (**§6.8**) is how AWS groups the same lessons into pillars.

| Fallacy (do **not** assume) | If you believe it | This estate |
| --- | --- | --- |
| **The network is reliable** | No retries, no health replace | Internal ALBs **fail closed** (5xx). ELB replaces unhealthy targets. CAP **P**: RDS can be unreachable. Use TCP/HTTPS/Bolt as they are — they cope with loss; we do not pretend the path never dies. |
| **Latency is zero** | Chatty calls, ignore p99 | Portal ALB → portal → REST ALB → RDS/Haystack/Bolt **adds hops**. Region is `us-east-1`, not a global edge. Measure **p99**, not “instant.” |
| **Bandwidth is infinite** | Huge payloads, pull Docker Hub every start | Finite: no NAT Gateway; ECR **in-region**; `desired=1`; Secrets Manager JSON is small. Congestion is real on a `t3` NAT instance. |
| **The network is secure** | Open 8080 “because it’s a VPC” | VPC ≠ safe. Private APIs, SGs, Secrets Manager, no `sk_` on the portal, SSM not public `:22`. Defense in depth. |
| **Topology doesn’t change** | Pin instance IPs | ASG **replace**; Vocareum stop/start; IPs change. Clients use **ALB DNS**. `configure-only` after Start Lab. Bolt URI is rewritten in SM. |
| **There is one administrator** | One person, one console | CI vs CD; academy vs paid; Terraform vs Ansible; `LabRole` vs humans. Modules (§6.9) so repair is not one god-box. |
| **Transport cost is zero** | Ignore ALB/NAT/ECR in the budget | ALB **hourly**, NAT instance, image pull, §3.1 credits after session end. Transport is **on the bill**. |
| **The network is homogeneous** | One protocol, one OS | ALB + RDS + Bolt + SSM + Actions + Vocareum. Interop: DNS, JDBC, Bolt, `get-secret-value`. Do not assume every hop is Amazon Linux HTTP. |

Neglecting these yields outages, slow tails, inconsistent data, leaks, scale surprises, and “who owns this?” **§6.8** maps the same ideas: Operational excellence → single administrator / homogeneous network; Security → secure network; Reliability → reliable network / fixed topology; Performance efficiency → zero latency / infinite bandwidth; Cost optimization and Sustainability → zero transport cost.

### 6.11 Adherence review

The **current** Academy (§6) and paid (§6P) design **adheres** to the Well-Architected Framework **as this study uses it** (§6.8: guideline + use case) and to §6.6–§6.10. It does **not** “pass” every WAF best practice. Doing so (Multi-AZ, OIDC, HTTPS, game days, X-Ray, EKS) would break KISS, credits, and Vocareum. WAF itself: **security and operational excellence are not traded away**; other pillars **are** traded for cost. That is **adherence**, not a defect.

This section is a **review snapshot** (conversation, not audit). Do not “fix” Academy by adding EKS or Multi-AZ.

#### What already meets the bars

| Bar | How the design meets it |
| --- | --- |
| **Isolation** (§6.9) | Four ASGs, three subnet tiers, dedicated internal ALBs, one secret per role |
| **KISS** (§6.9) | No EKS, CDK+TF, Marketplace Neo4j CFT, second RDS, NAT Gateway, CPU scale-out |
| **Metrics** (§6.9) | ALB 5xx, p99, RDS CPU, InService, budget, `assert-lab` |
| **TINSTAAFL / depends** (§6.7, §6.9) | Catalogued lunches; two use cases |
| **Fallacies** (§6.10) | Fail closed, ALB DNS, SM, private APIs, transport on the bill |
| **WAF Security** | Private data, SGs, LabRole, Stripe split, no public APIs — **not** traded |
| **WAF Operational excellence** | Terraform + Ansible in Actions; `plan` / `apply` / `configure-only` / `stop` / `destroy` |
| **WAF Reliability** (within cost) | ELB replace, ALB DNS, Neo4j rebuildable, `action=stop` |
| **WAF Performance / Cost / Sustainability** | Right-sized `t3.*`, ECR in-region, stop idle compute, no always-on EKS/NAT GW |

#### Accepted risks (not defects)

| Risk | Why we keep it |
| --- | --- |
| Single-AZ RDS / Neo4j `max=1` | Academy forbids Multi-AZ; credits |
| HTTP on portal unless ACM | Cannot mint a cert for `*.elb.amazonaws.com` |
| Vocareum access keys (no OIDC) | Cannot create an IdP |
| Shared `LabRole` can read every SM secret the role allows | Cannot create per-ASG instance profiles. Convention + paid isolation (§6.0c) |
| `desired=1`, scale policies off | Credits / instance cap |
| Idle ALB hours; no ElastiCache | KISS + §3.1 |
| No game days / WA Tool on lab | Class effort |

#### Adherence gates (do not regress)

- No public REST, Haystack, RDS, or Bolt
- No Neo4j sidecar on haystack as the **default**
- No PEM in Terraform / no `put-secret-value` of PEMs **before** InService
- No `STRIPE_SECRET_KEY` on the portal
- `destroy` only on `workflow_dispatch` + `confirm_destroy=destroy`; academy state ≠ paid state
- No CDK + Terraform on the same VPC
- No Marketplace Neo4j CloudFormation stack

#### Optional low-cost hygiene (if the lab allows)

Not new products and not new IAM: **encrypt RDS and EBS at rest** if the console/API permits; CD **creates** CloudWatch **alarms** on public-ALB 5xx and RDS CPU (SNS optional). Skip if the allow-list blocks them.

---

## 6P. Recommended architecture (Paid AWS)

System design principles: **§6.6**. Trade-offs: **§6.7**. Well-Architected: **§6.8**. Guidelines: **§6.9**. Fallacies: **§6.10**. Adherence: **§6.11**. This section is the paid **topology**. Same compose mapping and **same three subnet tiers**. **A different AWS account, Terraform state, GitHub Environment (`paid`), and workflow** (`aws-infra-paid.yml`). Do not share a VPC or state with Academy.

Auth is **GitHub OIDC** → IAM role `github-actions-infra`. No Vocareum keys. The account **may** create IAM roles and instance profiles.

Two AZs of **subnets**. Default is still **one Neo4j** (`max=1`). RDS may be Multi-AZ (primary + **standby**, not two writers). An optional **second** RDS for Haystack pgvector uses the **same data subnet group**.

```
                         Internet
                             │
                      Internet Gateway (IGW)
                             │
         ┌───────────────────┴──────────────────────────────────────────────┐
         │                     VPC  (paid account)                          │
         │                                                                  │
         │   public subnets (2 AZs)                                         │
         │   ┌───────────────────────────────────────────────────────────┐  │
         │   │ Public ALB  portal only   HTTPS :443  (HTTP → 443)        │  │
         │   │ NO /api  NO /haystack  NO 5432  NO 7687                   │  │
         │   └──────────────────────────┬────────────────────────────────┘  │
         │                              │ target HTTP :80                   │
         │   private APP subnets (2 AZs)                                    │
         │   ┌──────────────────────────┴────────────────────────────────┐  │
         │   │ ASG portal          Internal ALB REST :8080               │  │
         │   │                     Internal ALB Haystack :8000           │  │
         │   │ ASG rest ────────────────────────────────► ASG haystack   │  │
         │   │ (sync/populate on haystack; no Neo4j)                     │  │
         │   └──────────────┬─────────────────────────────┬──────────────┘  │
         │                  │ JDBC                        │ Bolt / JDBC     │
         │                  ▼                             ▼                 │
         │   private DATA subnets (2 AZs)  — no public IPs                  │
         │   ┌───────────────────────────────────────────────────────────┐  │
         │   │ RDS primary :5432     (+ Multi-AZ standby in the other AZ │  │
         │   │                         when enabled — still one writer)  │  │
         │   │ optional 2nd RDS (Haystack/pgvector) — same subnet group  │  │
         │   │ asg-neo4j  neo4j:5 or paid Marketplace AMI   Bolt :7687   │  │
         │   │ optional internal NLB for Bolt (not internet-facing)      │  │
         │   └───────────────────────────────────────────────────────────┘  │
         │   Outbound: NAT Gateway or VPC endpoints (paid may use either)   │
         └──────────────────────────────────────────────────────────────────┘
```

\*REST and Haystack stay on **dedicated internal** ALBs. Neo4j Bolt stays private. Do **not** run the vendor Marketplace CloudFormation stack (own VPC + public NLB/EIP).

### 6P.0 Same isolation rules as Academy

| Path | Allowed? |
| --- | --- |
| Public ALB rule to REST, Haystack, RDS, or Neo4j | **No** |
| Internet-facing ALB/NLB for REST, Haystack, or Bolt | **No** |
| Dedicated **internal** ALB for REST and for Haystack | **Yes** |
| Internal NLB for Neo4j Bolt | **Yes** (optional) |
| SSM port-forward | **Yes** — break-glass |

### 6P.0a Compute

Same four ASGs in the same tiers. Paid **may** create instance profiles (do not use `LabRole`). App ASGs may enable target-tracking later. **`asg-neo4j` stays `max=1`** (Community Edition, stateful). Desired counts can rise above 1 on portal/rest/haystack; Neo4j does not.

### 6P.0c Secrets

GitHub Environment **`paid`**: `AWS_ROLE_TO_ASSUME`, `AWS_REGION`, app passwords, Stripe keys. **No** `AWS_ACCESS_KEY_ID`. Same app secret ids **plus** `heavy-rental/ssh/{portal,rest,haystack,neo4j}` (key names `hr-paid-*`). `sync-secrets` writes Postgres + Stripe + ALB/RDS/Neo4j addresses. **`sync-ssh-keys` runs only after instances are InService** and writes PEMs.

### 6P.0b HTTPS

**Default HTTPS** on the public portal ALB (ACM in the ALB region). HTTP :80 redirects to :443. REST/Haystack/Bolt stay HTTP inside the VPC unless you later add a private CA (not required).

### 6P.1 What paid adds on the same topology

| Piece | Academy (§6) | Paid (§6P) |
| --- | --- | --- |
| Account / state | Vocareum lab | Separate billed account + state key |
| Auth | Environment access keys | OIDC role |
| IAM | `LabRole` only | May create roles / instance profiles |
| Subnet tiers | Public / app / data | **Same** |
| RDS | One, `multi_az = false` | One writer; **Multi-AZ standby** optional. Optional **second** RDS for pgvector — **same data subnet group** |
| Neo4j | `neo4j:5` container, `max=1` | Same default. Optional Marketplace **AMI in our data-subnet ASG** (not the vendor CFT). Optional internal Bolt NLB |
| Egress | NAT **instance** `t3.nano` or endpoints | NAT **Gateway** or endpoints |
| Public ALB | HTTP :80 typical | HTTPS :443 |
| Instance class | ≤ `large` | Larger classes allowed |
| ECS / EKS | Allowed, not default | Still not the default |

### 6P.2 VPC layout (paid)

Same example CIDRs as §6.2 (`10.0.0.0/24` public … `10.0.20.0/24` data). Differences:

- Data route table may use a **NAT Gateway** (or endpoints) instead of a NAT instance.
- RDS subnet group = **data subnets only**. Multi-AZ uses those two AZs as primary + standby — still **one** cluster, not one independent Postgres per AZ.
- Optional second RDS: same subnet group, still `publicly_accessible = false`.
- `asg-neo4j` still **one** instance. The second data subnet is not a second graph database.
- Security groups: same as §6.2. If an internal Bolt NLB exists, `sg-haystack` talks to the NLB SG; the NLB talks to `sg-neo4j:7687`.

### 6P.5 What paid must not do

- Share Terraform state or VPC with Academy
- Use Vocareum `LabRole` / `vockey` / lab access keys
- Run the Neo4j Marketplace **CloudFormation** stack (`prodview-a5jr6bo72f5aw`)
- Put RDS or Neo4j in public or app subnets
- Publish 5432, 7474, 7687, or 22 to the internet
- Put `STRIPE_SECRET_KEY` on the portal or bake `sk_` into the Vite image
- Mix CDK and Terraform on the same VPC
- Apply from app CI/Release workflows

---

## 7. Tooling: Actions is the pipeline; Terraform and Ansible are jobs

### 7.0 Split of responsibility

| Tool | Owns |
| --- | --- |
| **GitHub Actions** | **Trigger and orchestrator.** The only supported entry point to create, update, or tear down the VPC. Starts only when the Vocareum lab session is **already running**. |
| Terraform | VPC, **three subnet tiers**, SGs, **four ASGs** + launch templates, ALBs, RDS (data subnet group), ECR, **Secrets Manager secret resources** (empty shells) |
| **`sync-secrets` job** | `put-secret-value`: Postgres fields, Stripe, ALB/RDS/Neo4j addresses. **Not** SSH PEMs. |
| **`sync-ssh-keys` job** | **After** ASG instances are InService. Generate/load PEMs → `heavy-rental/ssh/*`. Install public keys via SSM. |
| **Ansible** | On each ASG: Docker + `get-secret-value` → `.env` + compose up; RDS `CREATE EXTENSION` |
| AWS CLI | Called by Actions (`configure-aws-credentials`, ECR login, optional stop/start). CloudShell is break-glass only. |
| **CI** (app Release) | Build, test, **create Docker images**, push GHCR / upload image tar. Does **not** apply Terraform. |
| **CD** (this study) | Consume those images; Terraform + sync-secrets + Ansible. Uses the **same GitHub Environment names and secret keys** the maintainer configured (copied onto the CD repo). Full walkthrough: **§8**. |

### 7.0a CI builds the image; CD uses the maintainer’s Environment copy

```
  Maintainer configures GitHub Environments
       academy  (Vocareum AWS keys + app secrets)
       paid     (app secrets + AWS_ROLE_TO_ASSUME; no Vocareum keys)
           │
           ├──────────────────────────────┐
           ▼                              ▼
  CI  (app repos / this pipeline-dev)   CD  (other project — this study)
  Release: docker build → GHCR / tar    Same Environment *copy* on the CD repo
  Does not apply AWS                    workflow_dispatch → terraform →
                                        sync-secrets → sync-ssh-keys (after InService) → Ansible
```

- **CI** = existing haystack / REST / portal **Release** pipelines. Output is the **Docker image** (and tar). Out of scope for VPC create.
- **CD** = `aws-infra-academy.yml` and `aws-infra-paid.yml`. This feasibility study is **only** CD.
- GitHub Environments are **per repository**. The maintainer **copies** `academy` and `paid` onto the CD repo: same Environment names, same secret **names**, same values (or the CD-specific AWS keys / OIDC vars). CI may use a subset (e.g. no Vocareum keys if it never calls AWS).
- CD **must not** invent different secret names. `sync-secrets` expects the same keys listed in §6.0c.
- Do not add `terraform apply` to `haystack-fast-api-pipeline/`. Do not put Academy and paid in one workflow.

Ansible is **not** an AWS service. Vocareum does not need to list it. The infra workflow installs Ansible on the runner (or uses a container that already has it). The pipeline-authoring devcontainer already includes the `ansible` feature for local dry-runs.

### 7.1 Terraform — primary IaC

Step-by-step of the GitHub Actions Terraform job (`plan` / `apply` / `destroy`, remote state, outputs): [`TERRAFORM-PROCESS.md`](TERRAFORM-PROCESS.md).

This pipeline-authoring devcontainer already installs Terraform, tflint, tfsec, and terraform-docs.

Terraform should own: VPC, **public + private-app + private-data** subnets, route tables, SGs, launch templates + **ASGs** (`asg-portal`, `asg-rest`, `asg-haystack` in app subnets; **`asg-neo4j` in data subnets**) with `LabInstanceProfile` (preferred: **no** `key_name` — PEMs come **after** InService), public ALB + `tg-portal`, **dedicated internal ALB** + `tg-rest`, **dedicated internal ALB** + `tg-haystack`, RDS in the **data subnet group only** (`publicly_accessible = false`), ECR, **`aws_secretsmanager_secret` shells** for `heavy-rental/{portal,rest,haystack,neo4j}` and `heavy-rental/ssh/*` (no plaintext passwords, Stripe secrets, or PEMs in `.tf` or state). Never a lone `aws_instance` outside an ASG (the NAT instance, if used, is the one documented exception — or wrap it in a 1-instance ASG). Never register REST or Haystack on the public listener. Never place RDS or `asg-neo4j` in the app or public subnets.

**Academy-specific rules for modules:**

- `iam_role` resources: **do not create**. Data-source `LabRole` / `LabInstanceProfile`. **`asg-neo4j` uses the same `LabInstanceProfile`.**
- No OIDC provider resource.
- No ECS/EKS resources.
- `region = us-east-1`.
- RDS: `multi_az = false`, no enhanced monitoring, class ≤ medium, subnet group = **data subnets only**.
- No `aws_nat_gateway`. No Marketplace AMI data source for Neo4j.
- `asg-neo4j`: `max_size = 1`, EC2 health only, scale-in protection.

**State backend (required for Actions):** S3 + DynamoDB lock (both are allow-listed). The GitHub runner is **ephemeral** — a local `terraform.tfstate` on the job is gone when the job ends; the next `apply`/`destroy` would orphan the VPC or fail. **Local state is CloudShell / laptop break-glass only.** Academy and paid use **different** bucket keys. The bucket itself is **not** in the same state (chicken-and-egg). Vocareum **Reset** deletes the bucket — keep `.tf` in Git and re-apply.

Do not use Terraform to install Docker or run `CREATE DATABASE`. That is Ansible.

Apply **only from GitHub Actions** while a Vocareum session is started. CloudShell/`terraform apply` on a laptop is break-glass, not the designed path.

### 7.1a Ansible — configure EC2 and sync RDS (yes)

**Yes, include Ansible.** It is the right tool to keep the EC2 guest and the RDS *contents* aligned after Terraform has created both.

Step-by-step inventory (when it runs, shared guest steps, per-group compose, RDS logical, app CD): [`ANSIBLE-PROCESS.md`](ANSIBLE-PROCESS.md).

What Ansible should do:

| Target | Playbook work |
| --- | --- |
| Each app ASG instance | Install Docker. **`aws secretsmanager get-secret-value`** for that role’s secret → `.env` → compose up with **§6.4a** `mem_limit`/`cpus`. Do not copy GitHub `secrets.*` onto the guest. Haystack compose **must not** start `neo4j`. |
| `asg-neo4j` | Install Docker. `get-secret-value` `heavy-rental/neo4j`. Compose **only** `neo4j:5` with `/data` on EBS. Bolt bound to the instance private IP (reachable from `sg-haystack`). |
| RDS (logical) | `community.postgresql` (or `ansible.builtin.command` + `psql`): create `heavy_rental` / Haystack DB if needed, roles, grants, `CREATE EXTENSION IF NOT EXISTS vector` |
| Sync workers | On **`asg-haystack`**: ensure `postgres-haystack-sync` and `neo4j-populate` are up and pointed at the **RDS endpoint** and the **`asg-neo4j` Bolt URI** — this **is** the compose “sync up”, not AWS DMS |

What Ansible should **not** do:

- Create the VPC, ALB, EC2 instance, or RDS **instance** (Terraform)
- Create IAM roles
- Treat RDS as a host in inventory (`ansible_host` = RDS will fail; there is no SSH guest OS)
- Open 5432 to the internet so the control node can migrate — prefer **running the Postgres modules from the EC2** (delegate_to the instance, which already has SG access to RDS)

Inventory / connection (Academy-friendly):

1. Terraform outputs each ASG name, the three ALB DNS names, the RDS endpoint, and the **Neo4j private IP / Bolt URI**
2. Ansible inventory is **four groups** (`portal`, `rest`, `haystack`, `neo4j`) via SSM (`LabRole`)
3. RDS SQL is `delegate_to` a **rest** or **haystack** instance (those SGs can reach RDS). Do not `delegate_to` Neo4j for Postgres. Do not open 5432 to the Actions runner.

Idempotency: re-run the playbook after every lab Start Lab (instances come back, public IPs may change, containers should `restart: unless-stopped`).

Optional overlap: **CodeDeploy** is allow-listed. Use it only if you want AWS-native deploys of a zip/revision. Do not run CodeDeploy **and** Ansible against the same files without a clear split.

### 7.2 Two Actions pipelines (Academy vs paid)

**GitHub Actions is the control plane.** There are **two pipeline types** — not one workflow with an account switch.

| | Academy pipeline | Paid AWS pipeline |
| --- | --- | --- |
| Workflow file | `.github/workflows/aws-infra-academy.yml` | `.github/workflows/aws-infra-paid.yml` |
| Example in this repo | [`aws-infra-pipeline.example.yml`](aws-infra-pipeline.example.yml) | [`aws-infra-paid-pipeline.example.yml`](aws-infra-paid-pipeline.example.yml) |
| GitHub Environment | **`academy`** | **`paid`** (optional later: `paid-staging`) |
| AWS account | Vocareum Learner Lab | Billed commercial account |
| How Actions authenticates | Environment secrets `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN` | **OIDC** → IAM role (e.g. `github-actions-infra`). No long-lived access keys |
| Terraform state | `s3://…/academy/…` or lab-local | Separate bucket/key, e.g. `s3://…/paid/…` |
| IAM in Terraform | **Do not create roles.** Use `LabRole` / `LabInstanceProfile` | May create task roles, instance profiles, OIDC provider (once, by an admin) |
| Shape | Same **three-tier VPC** (public / private-app / private-data). Four ASGs + 1× RDS in the data subnet group. NAT **instance** or VPC endpoints — **no NAT Gateway**, no Multi-AZ | Same three-tier mapping **plus** paid-only extras: Multi-AZ RDS, NAT Gateway or private+endpoints, ACM/HTTPS, optional second RDS (still in the **data** subnet group) / ECS / internal Bolt NLB |
| Who may run apply | People who can use Environment `academy` | Required reviewers on Environment `paid` |

Hard isolation:

- Academy jobs set `environment: academy` only. Paid jobs set `environment: paid` only.
- Academy workflow **must not** reference `secrets` from `paid` or assume the paid OIDC role.
- Paid workflow **must not** read `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_SESSION_TOKEN` (those are Vocareum-only).
- Different `concurrency` groups (`aws-infra-academy-…` vs `aws-infra-paid-…`).
- App Release never applies either; it only publishes images.

### 7.2a Academy pipeline — main trigger (Vocareum)

Nothing in the **lab** VPC is created except by `aws-infra-academy.yml` (plus Vocareum’s own stop/start of EC2).

```
  Start Lab in Vocareum  →  copy AWS Details
           │
           ▼
  GitHub → Settings → Environments → academy → Secrets
           (set/update the three values once per lab session)
           │
           ▼
  Actions → Run workflow  →  choose action only (no keys on the form)
           │
           ├─ job: assert-lab        environment: academy, sts get-caller-identity
           ├─ job: terraform         3 subnet tiers, 4 ASGs, ALBs, RDS, secret *shells* (no PEMs)
           ├─ job: sync-secrets      Postgres fields + Stripe + Neo4j/RDS/ALB addresses
           ├─ job: sync-ssh-keys     AFTER instances InService: PEM → heavy-rental/ssh/*
           └─ job: ansible           get-secret-value on each ASG + compose up (neo4j group ≠ haystack)
```

Copy-ready Academy workflow: [`aws-infra-pipeline.example.yml`](aws-infra-pipeline.example.yml).

#### Why Environment secrets beat typing keys on Run workflow

| | GitHub Environment `academy` secrets **(chosen)** | Type keys on `workflow_dispatch` **(rejected)** |
| --- | --- | --- |
| Confidentiality | Encrypted at rest; injected as `secrets.*`; **not** printed on the run Inputs panel | GitHub has **no secret-typed input**. Key, secret, and token can appear on the run **Inputs** page for anyone who can see Actions |
| Logs | GitHub masks `secrets.*` automatically | You must `::add-mask::` yourself; easy to leak with `set -x` or a debug action |
| Protection rules | Environment can require reviewers, wait timer, or selected branches before apply | Anyone who can dispatch the workflow can apply if they have keys |
| Vocareum rotation | Update the three Environment secrets after Start Lab, then Run | Paste three fields every run (fewer clicks, worse leak) |
| Stale credentials | Possible if you forget to update secrets | Always “fresh” if the operator pastes this session’s Details |
| Fit for Academy | Extra Settings click once per session | Matches “paste and go” but is the weaker security design |

**Decision:** GitHub Environment **`academy`** plus **optional Run-workflow fields** for the three Vocareum values. Those tokens **change every Start Lab**, so the operator may paste them on the form instead of editing Environment secrets each session. **Paid must not have these fields** (OIDC only).

OIDC remains impossible on Academy (cannot create an identity provider). GitHub cannot secret-type dispatch inputs — they may appear on the run **Inputs** page. Mask in logs (`::add-mask::`), `set +x`, private repo, Environment reviewers.

#### Authentication (Vocareum / Academy only)

Create **Settings → Environments → `academy`**. Optional fallback secrets (if the form is left empty):

| Secret | Source |
| --- | --- |
| `AWS_ACCESS_KEY_ID` | Vocareum **AWS Details** |
| `AWS_SECRET_ACCESS_KEY` | same |
| `AWS_SESSION_TOKEN` | same (almost always present) |

Optional Environment **variable**: `AWS_REGION=us-east-1`.

**Resolve order** (every Academy AWS job):

1. If `inputs.aws_access_key_id`, `aws_secret_access_key`, and `aws_session_token` are all set → use the form; `::add-mask::` each.
2. Else use Environment `secrets.AWS_*`.
3. Else fail: “Start Lab. Paste AWS Details on the form or set Environment academy.”

Also: `environment: academy` on every AWS job (reviewers + fallback + `AWS_REGION`). Never store the three Vocareum values in Secrets Manager or on the guest. Never add these inputs to **paid** workflows.

```yaml
on:
  workflow_dispatch:
    inputs:
      action:
        type: choice
        options: [plan, apply, configure-only, stop, destroy]
      aws_environment:
        type: environment
        default: academy
      aws_access_key_id: { type: string, required: false }
      aws_secret_access_key: { type: string, required: false }
      aws_session_token: { type: string, required: false }
```

Resolve form → else Environment `secrets.AWS_*` → `::add-mask::` → `configure-aws-credentials`. **Paid YAML must not declare these three inputs.**

**Session rule:** Start Lab → Run workflow → paste AWS Details on the form (or refresh Environment `academy`). If `ExpiredToken`, paste a fresh token. Do not apply on a dead session.

Enable Environment protection (required reviewers) if more than one person can apply.

#### Triggers (infra repo)

| Event | What it does |
| --- | --- |
| **`workflow_dispatch`** | **The only path in the example YAML.** Form: `action` + Environment + `confirm_destroy` when wiping. **No AWS key fields.** |
| Push / PR | **Not in the stub.** A later `terraform plan` on a trusted branch is optional. Apply is never implicit. |

Do **not** `apply` on every push. A bad apply spends lab credits and can disable the account.

#### Job graph (infra workflow)

Matches [`aws-infra-pipeline.example.yml`](aws-infra-pipeline.example.yml) / paid. Stubs for apply/compose/stop/destroy must **fail closed** until the other project replaces them.

1. **assert-lab** — `environment: academy`; `aws sts get-caller-identity`; fail with “Start Lab and update Environment secrets” on `ExpiredToken` or missing AWS keys.
2. **terraform** — `action=plan` or `apply` only. Create/update VPC, **three subnet tiers**, four ASGs, ALBs, RDS, **secret shells**. **No PEMs.** Remote state (§7.1).
3. **sync-secrets** — `needs: [terraform]` on apply (and on `configure-only` after assert). `put-secret-value` for `heavy-rental/{portal,rest,haystack,neo4j}`. **Does not write SSH PEMs.**
4. **sync-ssh-keys** — `needs: [terraform]`. **Wait until each ASG has an InService instance.** Then PEMs → `heavy-rental/ssh/*`. Skip if desired=0.
5. **ansible** — `needs: [sync-secrets, sync-ssh-keys]`. SSM; `get-secret-value`; compose with §6.4a limits + portal `/api` proxy.
6. **stop** — `action=stop` only. ASG desired=0 (all four + NAT) and `aws rds stop-db-instance`.
7. **destroy** — `action=destroy` only. `terraform destroy` of **this** state. Requires `confirm_destroy=destroy`. See **§7.2d**.

Optional later: a **summary** step that prints public portal ALB DNS and secret **ARNs** only — never passwords, Stripe secrets, PEMs, or public API URLs. Not in the stub YAML.

App **CI** Release workflows stay as they are (package + GHCR). They do not apply CD. They do not pass AWS keys. CD pulls the image CI already published.

#### What Actions must not do

- Create IAM roles or an OIDC provider
- `terraform apply` when the lab session is down or Environment secrets are missing
- Put AWS keys on **paid** `workflow_dispatch` (Vocareum form keys are Academy-only; mask them; never write them to SM)
- Commit Vocareum keys or store them as **repository** secrets (use Environment `academy` only)
- Mix CDK apply into the same workflow
- Recreate RDS on every image deploy (that is `configure-only`)
- Register REST or Haystack on the public ALB, or create an internet-facing ALB for either API
- Launch an EC2 that is not in an Auto Scaling group
- Place RDS or `asg-neo4j` in the public or private-**app** subnets
- Create a NAT Gateway, a Marketplace Neo4j AMI, or a new IAM role for Neo4j
- Publish 5432, 7474, or 7687 to `0.0.0.0/0`
- Call or reuse the **paid** workflow, Environment, or Terraform state

### 7.2b Paid AWS pipeline — separate type

**A second workflow** (`aws-infra-paid.yml`) is the only apply path for the billed account. Same job names (assert → terraform → sync-secrets → **sync-ssh-keys after InService** → ansible) and the same compose-to-VPC idea; different trust, scale, and isolation.

```
  GitHub Environment paid  (OIDC role ARN + region as variables)
           │
           ▼
  Actions → Run workflow aws-infra-paid.yml  →  action + environment=paid
           │
           ├─ job: assert-account    environment: paid, OIDC, sts get-caller-identity
           ├─ job: terraform         paid state key; 3-tier VPC; may create IAM roles
           └─ job: ansible           four ASG groups + RDS logical sync
```

#### Authentication (Environment `paid`) — OIDC, not Vocareum keys

A paid account **can** create an IAM OIDC identity provider for GitHub. That is the designed auth.

One-time (admin, not this workflow’s first student run):

1. Create GitHub OIDC provider in the paid account (`token.actions.githubusercontent.com`).
2. Create role `github-actions-infra` trusted only for this repo and `aws-infra-paid.yml`.
3. Put on Environment **`paid`**:
   - **Variable** `AWS_ROLE_TO_ASSUME` = role ARN
   - **Variable** `AWS_REGION`
   - Secrets for app data only (DB passwords, never `AWS_ACCESS_KEY_ID`)

```yaml
# aws-infra-paid.yml — do not copy academy key secrets into this file
on:
  workflow_dispatch:
    inputs:
      action:
        type: choice
        options: [plan, apply, configure-only, stop, destroy]
      aws_environment:
        type: environment
        default: paid

permissions:
  id-token: write   # required for OIDC
  contents: read

jobs:
  assert-account:
    environment: ${{ inputs.aws_environment }}
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ vars.AWS_ROLE_TO_ASSUME }}
          aws-region: ${{ vars.AWS_REGION }}
      - run: aws sts get-caller-identity
```

**Retrieval contract (paid):** jobs MUST use `environment: paid` and `vars.AWS_ROLE_TO_ASSUME`. They MUST NOT reference `secrets.AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, or `AWS_SESSION_TOKEN`. App passwords still come from Environment `paid` **secrets** into **`sync-secrets`**, then instances read Secrets Manager.

Enable Environment protection (required reviewers) on `paid` before the first apply.

#### What the paid pipeline may do that Academy must not

- Create IAM roles and instance profiles (task role, deploy role already exists)
- Multi-AZ RDS, larger instance classes, NAT Gateway or VPC endpoints — **still in the same three-tier layout**
- Second RDS for Haystack pgvector (compose isolation) — **same data subnet group**, never a public or app subnet
- Optional internal **NLB** for Neo4j Bolt (paid only). Academy uses the instance private IP in Secrets Manager.
- Optional Neo4j Marketplace **AMI** inside **our** data-subnet `asg-neo4j` (see §6.2b). Never the vendor CloudFormation stack.
- ACM certificate + HTTPS on the **public portal** ALB only. REST and Haystack stay on **dedicated internal** ALBs.
- ECR in the paid account as the runtime registry
- Later: ECS/Fargate or EKS **only if** you outgrow Compose-on-EC2 — still not the default

#### What the paid pipeline still must not do

- Share Terraform state or VPC with Academy
- Use Vocareum `LabRole` / `vockey`
- Apply from app CI/Release workflows
- Type AWS keys on the Run workflow form
- Mix CDK and Terraform on the same VPC
- Place RDS or Neo4j in public or app subnets (paid extras stay in the **data** tier)

Copy-ready paid workflow: [`aws-infra-paid-pipeline.example.yml`](aws-infra-paid-pipeline.example.yml).

### 7.2c Maintainer CD checklist — what this study is enough for

**Enough to configure GitHub Actions CD** (Environments, secrets, workflow files, how to Run). **Not enough to `apply` a real VPC.** Terraform and Ansible jobs in the example YAML are **stubs**. Status of this file: study only — no live IaC.

| The maintainer can do today | Where |
| --- | --- |
| Create Environments **`academy`** and **`paid`** on the **CD** repo | §7.2, §6.0c inventory |
| Set Vocareum keys on `academy` (not on the Run form) | §7.2a |
| Set `AWS_ROLE_TO_ASSUME` + `AWS_REGION` on `paid` (OIDC; no Vocareum keys) | §7.2b |
| Set app secrets: `SPRING_DATASOURCE_PASSWORD`, `NEO4J_PASSWORD`, Stripe trio | §6.0c |
| Copy example YAML → `.github/workflows/aws-infra-academy.yml` / `aws-infra-paid.yml` | This folder |
| Dispatch `plan` / `apply` / `configure-only` / `stop` / `destroy` | Job graph, §7.2d |
| Keep isolation: two files, two states, no key mix | §7.2 |
| Know the target architecture | §6–§6P |

| The other project must still write | Why |
| --- | --- |
| Terraform modules (VPC, four ASGs, ALBs, RDS, secret **shells**) | Placeholders only |
| `sync-secrets` JSON + `put-secret-value` | Stub |
| `sync-ssh-keys` wait-for-InService + PEM | Stub |
| Ansible inventory / playbooks | Stub |
| S3 + DynamoDB **remote** state (separate keys per account) | Required on Actions (§7.1). Exact bucket name is other-project |
| Exact GHCR image refs/tags to pull | CI publishes; CD must pin |
| Paid OIDC **trust-policy** JSON | Steps exist; not a copy-paste policy |
| Map REST CI `REST_API_CLOUD_DB_*` → CD `POSTGRES_*` | Names **differ** (§6.0c) |
| `terraform destroy` against the same backend as apply | Stub in example YAML; must empty **this** state only (§7.2d) |

### 7.2d `action=destroy` — remove everything Terraform created

**`destroy` is an infra CD action on both Academy and paid workflows.** It is **not** app CD. Haystack / REST / portal app CD must **fail** after a successful destroy (`asg-*` missing) — that is correct.

#### What it does

```
assert-lab / assert-account
        │
        ▼
confirm_destroy == "destroy"   (else fail — do not touch AWS)
        │
        ▼
terraform init   (same backend + state key as apply)
terraform destroy -auto-approve
```

One job. No Ansible. No `sync-secrets`. No `stop` first (destroy terminates instances and deletes RDS). Timeout **45–60 minutes** (RDS + ALB deletion is slow).

Terraform’s dependency graph is the order. Do **not** hand-delete ASGs or the VPC in the console and then expect state to match. Do **not** tag-scan the account and delete “everything named heavy-rental” — that can hit resources **not** in this state (or the other pipeline).

#### What it removes (if it is in **this** state)

| Resource Terraform created | After destroy |
| --- | --- |
| VPC, IGW, public / private-app / private-data subnets, route tables | **Gone** |
| NAT instance (Academy) or NAT Gateway (paid, if in state) | **Gone** |
| `asg-portal`, `asg-rest`, `asg-haystack`, `asg-neo4j` + launch templates + EC2 | **Terminated / gone** |
| Public portal ALB + both internal ALBs + listeners + target groups | **Gone** (hourly ALB charge stops) |
| RDS instance + TF-created subnet / parameter / option groups | **Deleted** (data **irrecoverable**) |
| Security groups | **Gone** |
| Secrets Manager shells `heavy-rental/{portal,rest,haystack,neo4j}` and `heavy-rental/ssh/*` | **Deleted** (including PEMs) |
| ECR repositories Terraform created (and images in them) | **Gone** |
| CloudWatch log groups / alarms Terraform created | **Gone** |
| Paid extras in that state (second RDS, Bolt NLB, ACM listener, IAM roles TF created) | **Gone** |

Academy RDS: set `deletion_protection = false` so destroy can succeed. Secrets Manager: `recovery_window_in_days = 0` (or force-delete) so the secret is actually removed, not scheduled.

#### What it does **not** remove

| Left behind | Why |
| --- | --- |
| GitHub Environments `academy` / `paid` and their secrets | Not AWS; needed for the next `apply` |
| GHCR images / CI zips / tars | Not in Terraform; CI owns them |
| Vocareum `LabRole` / `LabInstanceProfile` | Pre-created by the lab; our TF must never create IAM on Academy |
| S3 / DynamoDB **Terraform state backend** | Chicken-and-egg; destroy empties the **state object**, it does not delete the bucket |
| Manual console resources not in state | Not Terraform’s |
| The **other** account / state | Academy destroy never touches paid. Paid destroy never touches Academy |

If the backend is empty or state is missing (Vocareum **Reset** already wiped the account), **fail closed**: “nothing to destroy / state missing.” Do not invent a second destroy path.

#### `stop` vs `destroy`

| | `action=stop` | `action=destroy` |
| --- | --- | --- |
| Intent | Pause for the lab day | Wipe the estate |
| ASGs | desired=0 or instances stopped | Groups **deleted** |
| RDS | **Stopped** (storage still bills; AWS auto-starts in 7 days) | **Deleted** |
| ALBs / VPC / secret shells | **Stay** (ALBs still bill) | **Deleted** |
| Next run | Start Lab + `configure-only` | `apply` from scratch |
| When | End of each lab day (§3.1) | End of class, failed estate, or credits must go to zero |

#### Safety

- `workflow_dispatch` only. Never destroy on push/PR.
- Input `confirm_destroy` must equal the literal string `destroy`. Empty or any other value → fail before `terraform init`.
- Same GitHub Environment and **same state key** as that pipeline’s `apply`.
- Environment required reviewers on **paid** (and on `academy` if more than one operator).
- `set +x`. Do not print secret values while secrets are being deleted.
- After destroy, app CD (`asg-portal` / `asg-rest` / `asg-haystack`) fails until the next infra `apply`. That is expected.

### 7.2e Validation (design vs execution)

**Design (this folder) is consistent** on: Academy vs paid isolation; three subnet tiers; four ASGs; portal-only public ALB; nginx `/api` → REST ALB → `asg-rest` → Haystack ALB :8000; Haystack → RDS :5432 and Bolt :7687; one Academy RDS (not REST-exclusive); `stop` vs `destroy`; CI image contract (ports 80 / 8080 / 8000).

**Example workflows cannot apply or deploy.** Terraform, Ansible, image load, `stop`, and `destroy` steps are stubs and **must exit 1** until the other project replaces them. Discover / `assert-*` / `confirm_destroy` are real fail-closed checks.

**Would fail at implement time if ignored:**

| If you… | What happens |
| --- | --- |
| Keep Terraform state on the runner | Next job has no state; `destroy` cannot empty the estate |
| Treat LabRole as per-ASG IAM | Portal can read `heavy-rental/rest` if LabRole can |
| `docker compose` the CI portal image as-is | No `/api` proxy; browser cannot reach REST |
| Pull GHCR on Academy without a token / ECR copy | `LabRole` is ECR pull-only; GHCR is private |
| Copy stub YAML and treat a green run as success | Nothing was created or destroyed |

Caps: desired 1+1+1+1 + nano NAT = 5 ≤ 9; max 2+2+2+1+1 = 9.

### 7.3 AWS CLI — operator surface

The CLI runs **on the Actions runner** after `configure-aws-credentials`. Same commands for debug in Vocareum CloudShell if a job fails:

- `aws sts get-caller-identity`, `aws ec2 describe-instances`, `aws rds stop-db-instance`
- SSM: `aws ssm start-session` onto an app or Neo4j instance (`asg-neo4j` has no public IP)

The CLI is not the source of truth and is not the trigger.

### 7.4 AWS CDK — alternative, not a hybrid

CloudFormation **is** allowed, so CDK *can* synthesize and deploy.

Do **not** run CDK and Terraform against the same VPC.

CDK’s default constructs create IAM roles, log groups, and sometimes extra VPCs. Those **fail** or violate the IAM rule. A CDK path would need the same discipline: attach `LabRole`, no new roles.

Given this repo’s Terraform toolchain, **do not introduce CDK** unless the other project is TypeScript-first and drops Terraform entirely.

---

## 8. End-to-end flow (CI then CD)

Still implemented in the other project. **CI first (image), then one infra CD per account.** Example workflows are fail-closed stubs.

This section is the single walkthrough. Terraform job detail is **first** (from [`TERRAFORM-PROCESS.md`](TERRAFORM-PROCESS.md)), then guest compose (from [`ANSIBLE-PROCESS.md`](ANSIBLE-PROCESS.md)).

```
CI Release (already exists)
    → images: portal :80 · REST :8080 · Haystack :8000

One-time: Environments + remote state + copy YAML   (§8.0)

Infra CD  action=apply
    assert-lab / assert-account
    terraform     init → plan → apply               (§8.1)
    sync-secrets  +  sync-ssh-keys                  (§8.2)
    ansible       four groups, SSM                  (§8.3)

Runtime: Browser → public portal ALB → …            (§8.4)
Later: plan / configure-only / stop / destroy / app CD  (§8.5)
Paid: same jobs, OIDC, different state              (§8.6)
App CD auth: academy three keys on Environment only (§8.7)
```

### 8.0 One-time setup (human, before any run)

**GitHub (CD repo)**

- Copy Environments **`academy`** and **`paid`** onto the CD repo (GitHub does not share Environments across repos).
- **`academy`:** fallback secrets `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN` (or paste them on Run workflow — they change every Start Lab). Also `SPRING_DATASOURCE_PASSWORD`, `NEO4J_PASSWORD`, Stripe trio. Variable: `AWS_REGION`. **Vocareum only.**
- **`paid`:** variables `AWS_ROLE_TO_ASSUME` + `AWS_REGION`. Same **app** secrets. **No** Vocareum access keys. Admin has already created GitHub OIDC + role `github-actions-infra`.
- Copy [`aws-infra-pipeline.example.yml`](aws-infra-pipeline.example.yml) → `.github/workflows/aws-infra-academy.yml` and [`aws-infra-paid-pipeline.example.yml`](aws-infra-paid-pipeline.example.yml) → `aws-infra-paid.yml`.
- Optional later: app CD workflows (portal / REST / Haystack). They do **not** create the estate.
- Optional: Environment variable `IMAGE_HTTP_URL` (HTTPS tar). **Academy** may paste Vocareum keys on the Run form; **paid must not**.

**CI (already exists)** — Release pipelines produce:

| App | Image | Port |
| --- | --- | --- |
| Portal | nginx + Vite `dist/` tar / GHCR | 80 |
| REST | Tomcat + WAR tar / GHCR | 8080 |
| Haystack | uvicorn tar / GHCR | 8000 |

CI Environments (`integration` / `production` or none) are **not** CD `academy` / `paid`.

**Remote Terraform state (required):** S3 + DynamoDB lock. Academy key ≠ paid key. The GitHub runner is ephemeral — a local `tfstate` dies with the job.

---

### 8.1 Terraform in GitHub Actions (first)

Full contract: [`TERRAFORM-PROCESS.md`](TERRAFORM-PROCESS.md). Terraform runs **only on infra CD**. App CD never calls it.

#### Which workflow

| Workflow (copy name) | Environment | Auth |
| --- | --- | --- |
| `aws-infra-academy.yml` | `academy` | Vocareum access key + secret + **session token** |
| `aws-infra-paid.yml` | `paid` | OIDC `vars.AWS_ROLE_TO_ASSUME` (`id-token: write`) |

Trigger: **`workflow_dispatch` only**. Form: `action`, `aws_environment`, `confirm_destroy` when wiping, and on **Academy only** the three Vocareum keys (optional if Environment `academy` is set). **Paid has no key fields.** Academy: **Start Lab** then paste AWS Details. If `sts` fails (`ExpiredToken`), paste a fresh token.

#### When the Terraform job runs

| `action` | Terraform? | Commands on the runner |
| --- | --- | --- |
| `plan` | Job `terraform` | `init` → `plan` |
| `apply` | Job `terraform` | `init` → `plan` → `apply` |
| `destroy` | Job **`destroy`** (not the plan/apply job) | `confirm_destroy == destroy` → `init` → `destroy -auto-approve` |
| `configure-only` | **Skipped** | `sync-secrets` + `sync-ssh-keys` + Ansible only |
| `stop` | **Skipped** | AWS CLI: ASG desired=0 + `rds stop-db-instance` (not `terraform destroy`) |

Do **not** `apply` on push or pull_request. Timeouts in the examples: plan/apply **30** minutes; destroy **60** minutes.

#### Steps inside the `terraform` job (`plan` / `apply`)

```
assert-lab / assert-account          sts; refuse the wrong account
        │
        ▼
Job terraform   if: action == plan || apply
                environment: academy | paid
  1. configure-aws-credentials@v4    three Vocareum keys  OR  role-to-assume
  2. actions/checkout@v4             .tf from the CD repo
  3. terraform init                  S3 backend + DynamoDB lock  (required)
  4. terraform plan                  always; no apply on action=plan
  5. terraform apply                 only if action=apply
```

`configure-aws-credentials` and `checkout` are **Actions** steps. `init` / `plan` / `apply` are the **Terraform** process.

**Remote state:** `init` must use S3 + DynamoDB lock. Academy key ≠ paid key. The backend **bucket** is not in this state. Vocareum **Reset** deletes the bucket — keep `.tf` in Git and re-apply. Local state is CloudShell / laptop break-glass only.

#### What `apply` puts in that state

| In state (Terraform creates) | Not Terraform |
| --- | --- |
| VPC, IGW, three subnet tiers (2 AZs each), route tables | Docker / compose / `.env` |
| NAT **instance** (Academy; not NAT Gateway) | `CREATE DATABASE` / extensions |
| Security groups (portal / rest / haystack / neo4j / ALBs / RDS) | Stripe plaintext, DB passwords, PEMs |
| Four launch templates + ASGs (`LabInstanceProfile` on Academy) | CI images, GHCR, GitHub Environments |
| Public portal ALB + `tg-portal` :80 | `action=stop` (CLI) |
| Internal REST ALB + `tg-rest` :8080 | App CD deploys |
| Internal Haystack ALB + `tg-haystack` :8000 | |
| RDS in the **data** subnet group (`publicly_accessible=false`, `multi_az=false`, `deletion_protection=false`) | |
| Empty Secrets Manager shells `heavy-rental/{portal,rest,haystack,neo4j}` and `heavy-rental/ssh/*` | Secret **values** (`sync-secrets` / `sync-ssh-keys`) |
| Optional ECR repos | |

Preferred: **no** `key_name` on launch templates. PEMs wait until InService.

Academy `.tf` must not create IAM roles or an OIDC provider, must not use `aws_nat_gateway` or a Marketplace Neo4j CFT, and must not register REST/Haystack on the public listener. `asg-neo4j`: `max_size = 1`.

#### Destroy job (still Terraform, later)

```
assert-* → confirm_destroy == "destroy" → init (same backend/key) → destroy -auto-approve
```

No Ansible. No `stop` first. Same state as that pipeline’s `apply`. What is deleted: **§7.2d**.

---

### 8.2 After Terraform: `sync-secrets` and `sync-ssh-keys`

These are **not** Terraform and **not** Ansible.

**`sync-secrets`** builds JSON from Terraform **outputs** + GitHub Environment app secrets and `put-secret-value`s:

| Terraform output | Lands in |
| --- | --- |
| Internal REST ALB DNS | `heavy-rental/portal` → `REST_BASE_URL` (+ `STRIPE_PUBLISHABLE_KEY` only) |
| Internal Haystack ALB DNS | `heavy-rental/rest` → `HAYSTACK_URL` |
| RDS endpoint hostname + port | `heavy-rental/rest` and `heavy-rental/haystack` → `POSTGRES_*` / URL |
| `asg-neo4j` private IP | `heavy-rental/haystack` → `NEO4J_URI` (`bolt://…:7687`) |

REST also gets Stripe `sk_` + `whsec_` + `pk_`. Neo4j secret is user/password only. **`sync-secrets` fails** if host, database, password, or port is empty, or if portal is missing `REST_BASE_URL`, or if REST is missing `HAYSTACK_URL` when Haystack is in use. Do not echo SecretString, `sk_`, or PEMs. Do not write Vocareum AWS keys into Secrets Manager.

**Required AWS Secrets Manager parameters before any app CD `deploy`:**

| Secret id (Terraform shell) | Required JSON fields (`sync-secrets`) | Who reads |
| --- | --- | --- |
| `heavy-rental/portal` | `REST_BASE_URL`, `STRIPE_PUBLISHABLE_KEY` | `asg-portal` / portal app CD |
| `heavy-rental/rest` | `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DATABASE`, `POSTGRES_USERNAME`, `POSTGRES_PASSWORD`, `POSTGRES_URL` / `SPRING_DATASOURCE_*`, `HAYSTACK_URL`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PUBLISHABLE_KEY` | `asg-rest` / REST app CD |
| `heavy-rental/haystack` | Same Postgres field set (or Haystack db name), `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` | `asg-haystack` / Haystack app CD |
| `heavy-rental/neo4j` | `NEO4J_USER`, `NEO4J_PASSWORD` | `asg-neo4j` (infra/`configure-only` only) |

App CD does **not** create these secrets. It only `describe-secret` / the guest `get-secret-value`. If a required id or field is missing, **fail** and run infra `apply` or `configure-only` first.

**`sync-ssh-keys`:** wait until each ASG is **InService**. Then generate PEMs → `heavy-rental/ssh/*`, install **public** keys via SSM. Skip if desired=0. Never `tls_private_key` in Terraform.

---

### 8.3 Ansible on the guests (after secrets)

Full contract: [`ANSIBLE-PROCESS.md`](ANSIBLE-PROCESS.md). Ansible runs on `apply` and `configure-only`. It does **not** run on `stop` or `destroy`.

#### When and how it connects

```
Infra apply:     Terraform (EC2 InService) → sync-secrets → sync-ssh-keys → Ansible (all four groups)
configure-only:  sync-secrets + sync-ssh-keys + Ansible   (no terraform apply)
App CD later:    discover ASG → same playbook, one group (portal | rest | haystack). No terraform. No neo4j group.
```

1. Actions runner installs Ansible (or uses an image that has it).
2. Dynamic inventory: four groups — `portal`, `rest`, `haystack`, `neo4j`.
3. `ansible_connection=aws_ssm`; instance id from the ASG. No public IP. No `ansible_host`.
4. RDS is **not** in inventory (no SSH guest OS).
5. Everyday path is SSM. SSH PEM is break-glass only.

#### Shared guest steps (every ASG)

1. Reach the instance via SSM (`LabInstanceProfile` / paid instance profile).
2. Install Docker and the compose plugin if missing.
3. `aws secretsmanager get-secret-value` of **that role’s** app secret only.
4. Map JSON → `.env`; `chmod 600`.
5. Do **not** copy GitHub `secrets.*` onto the guest. Do **not** fetch `sk_` or PEMs onto `asg-portal`.
6. Load or pull the **CI** image (pipeline-configured; see below). Do not `docker build` / `npm` / `mvn`.
7. `docker compose up` with §6.4a `mem_limit` / `cpus`, `restart: unless-stopped`, no `replicas > 1`. Leave 256–512 MiB for OS + SSM + Docker.

**Image source is configured on the GitHub Actions workflow**, not hard-coded in Ansible. Resolution: `inputs.image_http_url` → else Environment `IMAGE_HTTP_URL` → else `image_ref` if it is `https://…` → else registry tag (`docker pull`) → else latest Release tar then `docker load`. Academy preferred HTTP path: **S3 HTTPS** + `LabRole` `GetObject`. No plain `http://` registry.

#### Per-group compose (infra first run)

| Group | Secret | Compose | Limits |
| --- | --- | --- | --- |
| `portal` | `heavy-rental/portal` (`REST_BASE_URL`, `pk_` only) | nginx :80; write `/api` → `REST_BASE_URL` (CI image has SPA `try_files` only). Fail if URL empty. Health `GET /`. Do not fail solely because `/api` is down. | `256m` / `0.5` |
| `rest` | `heavy-rental/rest` (Postgres, `HAYSTACK_URL`, Stripe trio) | Tomcat :8080. Health `/actuator/health` or `/`. No Bolt. | `1g` / `1.0` |
| `haystack` | `heavy-rental/haystack` (Postgres, `NEO4J_URI` not localhost) | uvicorn :8000 + `postgres-haystack-sync` + `neo4j-populate`. **Must not** start `neo4j`. Optional pgvector only on `t3.medium`. Health `/docs` or `/health`. | `768m` / `1.0` + two workers `256m` / `0.25` |
| `neo4j` | `heavy-rental/neo4j` | **Only** `neo4j:5`, `/data` on EBS, Bolt on private IP. No ALB. App CD does not run this group. | `4g` / `1.5`, heap 512m–1G |

**RDS logical** (`delegate_to` rest or haystack — not Neo4j, not the runner): `CREATE DATABASE heavy_rental`, roles/grants, optional `vector`. Recommended Academy Haystack DB is a **pgvector container** on `asg-haystack`, not a second RDS.

Ansible must not create the VPC/ASG/ALB/RDS **instance**/IAM, inventory RDS as a host, open `:5432` to the runner, start Neo4j on haystack, or put `sk_` on the portal.

---

### 8.4 Runtime (what apply + Ansible just built)

```
Browser  →  public portal ALB :80/:443
              →  asg-portal  (nginx SPA + /api proxy)
                    →  internal REST ALB :8080
                          →  asg-rest
                                →  RDS :5432          (SoR database heavy_rental)
                                →  internal Haystack ALB :8000   (HAYSTACK_URL)
                                      →  asg-haystack
                                            →  RDS :5432          (sync/populate; optional Haystack db)
                                            →  Neo4j Bolt :7687   (asg-neo4j; sg-haystack only)
```

Students use the **public portal ALB DNS** only. Operators use SSM.

---

### 8.5 After the first apply

| Goal | Workflow | `action` | Terraform? | Ansible? |
| --- | --- | --- | --- | --- |
| Preview `.tf` | Infra | `plan` | `init`+`plan` | No |
| New image / secret / after Start Lab | Infra | `configure-only` | **No** | Yes (all four groups) |
| Pause for the lab day | Infra | `stop` | **No** | No — ASG desired=0 + stop RDS |
| Wipe the estate | Infra | `destroy` + `confirm_destroy=destroy` | `destroy` | No |
| New portal / REST / Haystack image only | App CD | `deploy` | **No** | One group only |

**Next Start Lab:** instances come back; IPs change. Re-run **`configure-only`**. Do not recreate RDS. Session end does **not** stop RDS or ALB billing — use `stop` (§3.1).

**App CD** (after infra is up): discover `asg-*` (InService + SSM Online) → resolve image (`image_http_url` / `IMAGE_HTTP_URL` / `image_ref`) → same playbook, one group → health. Fail if the ASG is missing. Auth: **§8.7**. Required SM parameters: **§8.2**.

---

### 8.6 Paid (`aws-infra-paid.yml`)

Same job names and the same communication graph. Differences:

1. Admin has already created the GitHub OIDC provider and `github-actions-infra`. Environment **`paid`** holds `AWS_ROLE_TO_ASSUME` and `AWS_REGION`. No Vocareum keys.
2. **Terraform apply** uses the **paid** state key — same three-tier VPC; may include Multi-AZ, NAT Gateway, ACM HTTPS on the **portal** ALB, extra IAM, second RDS. RDS and Neo4j stay in the **data** subnets.
3. `sync-secrets` / Ansible run in the **paid** account only. Same required SM ids and fields as §8.2, in the **paid** account.
4. `action=destroy` on **this** workflow wipes **paid** state only. Never run Academy destroy against paid.

Do not bake keys into Git. App passwords start in GitHub Environment secrets, then live in **AWS Secrets Manager** in that same account.

### 8.7 App CD authentication (Academy three keys)

Portal, REST, and Haystack **app CD** deploy with the **same** Vocareum session as infra CD (**Academy / Vocareum only**). Paste the three keys on the Run form (they expire every Start Lab) or leave them empty and use Environment `academy`.

```
Actions runner  ←  form aws_access_key_id / secret / session_token
                     else Environment academy secrets
                     (Vocareum only — paid uses OIDC)
       │
       │  sts, describe-asg, ssm, secretsmanager describe
       │  optional: ecr:GetAuthorizationToken + docker push (Vocareum user can write ECR)
       ▼
EC2 (LabRole / LabInstanceProfile)
       ←  get-secret-value heavy-rental/{portal|rest|haystack}
       ←  docker load / ecr pull / HTTPS tar   (LabRole is ECR pull-only)
       ←  compose up
```

| The three keys **can** | The three keys **cannot** |
| --- | --- |
| Authenticate the **Academy runner** (form this session, or Environment fallback) | Appear on **paid** workflows (OIDC only) |
| `describe-secret` / prove SM ids from §8.2 exist | Push **GHCR** (that is CI `GITHUB_TOKEN`) |
| Discover `asg-*` + SSM deploy | Live on the EC2 or in Secrets Manager |
| Optional **ECR push** of the CI tar | Replace `LabRole` on the instance |

After **Start Lab**, paste fresh AWS Details on the **Academy** Run form (or refresh Environment `academy`). Copy Environment **`academy`** onto each app-CD repo. App passwords/Stripe on that copy are optional if infra already filled AWS.

Paid app CD: `AWS_ROLE_TO_ASSUME` only. **No** `aws_access_key_id` inputs. Workflows **fail** if `AWS_ACCESS_KEY_ID` is set.

---

## 9. Risks

| Risk | Why it matters on Academy | Mitigation |
| --- | --- | --- |
| IAM role creation | ECS/EKS/Fargate and many CDK/Terraform modules die | Only `LabRole` / `LabInstanceProfile` |
| Service allow-list drift | Educator Readme may differ from the PDF cited here | Re-check Vocareum Readme before locking modules |
| NAT Gateway cost | Can consume most of a $50 budget | Public-subnet EC2 + tight SGs, or skip NAT |
| Two RDS + Neo4j 24/7 | Credits vanish | One RDS in the **data** subnet group; Neo4j in Docker on `asg-neo4j`; `action=stop` for all four ASGs + RDS when the lab ends |
| Fourth ASG (`asg-neo4j`) | Extra instance vs the old sidecar design | Desired=1, `t3.large` is allow-listed. Still 4–5 instances ≪ 9. Fallback (not default): Neo4j back on haystack, **RDS still in data subnets**. |
| NAT Gateway “because data subnets” | Can consume most of a $50 budget | **Forbidden on Academy.** Shared `t3.nano` NAT instance or VPC endpoints. |
| Neo4j Marketplace AMI / [Community Edition CFT](https://aws.amazon.com/marketplace/pp/prodview-a5jr6bo72f5aw) | Vocareum forbids Marketplace; vendor stack also creates IAM, a second VPC, and a public NLB/EIP | Academy: `neo4j:5` container only. Paid: do **not** run the vendor CFT. Optional AMI-in-our-data-subnet later. See §6.2b. |
| Creating an IAM role for Neo4j | Vocareum forbids new roles | Same `LabInstanceProfile` as every other ASG |
| RDS in app subnets | Mixes data with compute; easier to expose 5432 | `aws_db_subnet_group` = data subnets only |
| Putting Neo4j on `asg-haystack` as the default | Graph store shares the app host; misses the data-tier requirement | Default is `asg-neo4j` in data subnets |
| Replacing `asg-neo4j` via ELB health | Stateful graph lost | `max=1`, EC2 health only, scale-in protection; rebuild from `neo4j-populate` |
| `pgvector` on RDS | Extension may be missing on the Academy engine version | Fallback: `pgvector/pgvector:pg17` container |
| Amazon Linux AMI only | Cannot launch Ubuntu AMIs | Docker images stay Debian/Ubuntu; host is Amazon Linux |
| Stale Environment secrets | Vocareum token expired after the last Start Lab | `assert-lab` before Terraform; update `academy` secrets then re-run |
| Typing keys on Run workflow | Inputs panel can leak the session token | Rejected design — Environment secrets only |
| Passwords only in GitHub, never on the instance | New ASG nodes have empty `.env` after scale-out | `sync-secrets` then `get-secret-value` in user-data/Ansible |
| Putting Vocareum AWS keys in Secrets Manager | Session tokens in the wrong place; leak via instance | GitHub Environment `academy` only for those three names |
| SSH PEM in `.tf`, Terraform state, or **before EC2 exists** | Leak, or a key nobody can use | Empty secret shells in TF. **`sync-ssh-keys` only after InService.** Never `tls_private_key`. |
| Public `:22` “because we have PEMs” | Internet can brute-force the ASGs | Deny `:22` from `0.0.0.0/0`. Everyday = SSM. PEM = break-glass + SSM port-forward |
| `STRIPE_SECRET_KEY` on the portal | Browser / nginx image can leak `sk_` | Portal secret = publishable key only. Secret + webhook on `heavy-rental/rest` only |
| REST or Haystack on the public ALB | Internet can hit the API / LLM stack | Dedicated **internal** ALBs only; SGs deny 8080/8000 from `sg-alb-public` and `0.0.0.0/0` |
| Lone EC2 without an ASG | Replace/scale is manual; no ELB-driven replace | Launch template + ASG for portal, REST, and Haystack |
| One workflow for both accounts | Academy keys or LabRole used against a billed account (or the reverse) | Two workflow files, two Environments, two state keys |
| Accidental apply on every push | Credits + possible account wipe | `apply` only on `workflow_dispatch`; PRs are `plan` only |
| Accidental `destroy` | RDS data and the VPC are **gone** | `confirm_destroy=destroy`; Environment reviewers; never on push/PR; academy state ≠ paid state |
| 4-hour session | Instances stop; public IPs change | ALB DNS; optional EIP; compose `restart: unless-stopped`; re-dispatch `configure-only` after Start Lab |
| Lab reset | Vocareum may wipe the account | Keep Terraform in Git; S3 state is gone after Reset — re-apply from code |
| Haystack image size | Slow pull on a small instance | Prefer ECR in-region; avoid pulling from GHCR on every start |
| Sync is poll, not CDC | Same as compose (`SYNC_INTERVAL_SECONDS=60`) | Keep the script; do not build DMS (not needed, and DMS is not listed) |
| Neo4j memory | `t3.medium` will OOM | `asg-neo4j` = `t3.large`; cap Neo4j heap as in compose (512m–1G). Do not size haystack for the graph. |

---

## 10. Cost / complexity (qualitative)

| Design | Fit for Academy credits | Ops complexity | Faithfulness to compose |
| --- | --- | --- | --- |
| **4 ASGs + public portal ALB + 2 internal ALBs + 1× RDS in data subnets** | Medium-high — stop daily | Medium | High (apps vs data split) |
| EC2 + Compose only (Postgres in Docker) | Lowest | Lowest | High |
| ECS Fargate + 2× RDS | High cost; allowed only with `LabRole` | Medium | Medium |
| EKS | Allowed (`LabEksClusterRole`); highest cost | Highest | Low |

---

## 11. Phased path

### 11.1 Academy (class)

All phases run through **`aws-infra-academy.yml`**, after Start Lab.

1. Workflow skeleton: Environment `academy` + `workflow_dispatch` (`action` only) + `assert-lab` + `terraform plan`.
2. `action=apply`: VPC + **public + private-app + private-data** subnets + SGs + **four ASGs** + public portal ALB + **dedicated internal REST ALB** + **dedicated internal Haystack ALB** + RDS in the **data subnet group** + `asg-neo4j` in the data subnets.
3. Ansible: Docker on each ASG + release images + RDS logical setup. Portal must not receive a public REST URL. Haystack compose must not start Neo4j.
4. Haystack ASG workers only: optional pgvector + sync + populate, pointed at RDS and **`asg-neo4j` Bolt**. No public `/api` or `/haystack` rule.
5. ECR in the lab account (including a copy of `neo4j:5` so the data-subnet host does not need Docker Hub).
6. `action=stop`: set all four ASG desired=0 (or stop instances) and stop RDS.
7. `action=destroy`: `terraform destroy` of the Academy state — VPC, ASGs, ALBs, RDS, secret shells, NAT instance. Requires `confirm_destroy=destroy`. See §7.2d.

Do not add a second RDS, NAT Gateway, Marketplace Neo4j AMI, a new IAM role, or EKS on Academy. Do not put REST, Haystack, RDS, or Neo4j on a public address. Do not place RDS or Neo4j in the app subnets.

### 11.2 Paid (separate, after Academy works)

All phases run through **`aws-infra-paid.yml`**. Do not promote Academy state.

1. Admin: OIDC provider + `github-actions-infra` + Environment `paid` (reviewers on).
2. Plan against an empty paid state key.
3. Apply a **new** VPC (same **three-tier** topology; paid extras allowed — Multi-AZ / second RDS / Bolt NLB still land in the **data** subnets).
4. Ansible against paid outputs; images from paid ECR.
5. Only then consider Multi-AZ, HTTPS, or a second RDS.
6. `action=destroy` on the **paid** workflow wipes **paid** state only.

---

## 12. Open questions for the other project

1. Exact lab product: **Foundation Services** vs a custom educator allow-list (does *your* Readme mention ECS)?
2. Credit amount ($50 vs $100) and whether the lab is wiped between assignments.
3. Region preference (`us-east-1` recommended).
4. Public portal ALB: HTTP-only until a domain exists; then ACM + HTTPS :443 + 80→443 redirect.
5. Confirm `CREATE EXTENSION vector` on the lab’s RDS Postgres version; if unknown, plan the pgvector container from day one.
6. Whether Neo4j Browser must be reachable from the student laptop (if yes: SSM port forward, never `0.0.0.0/7474`).
7. Who can edit Environment `academy` secrets and who can approve apply (Environment protection)?
8. Confirm Vocareum AWS Details always includes a session token (almost always yes).
9. Paid account ID, region, and who may approve Environment `paid` applies.
10. Whether paid keeps four ASGs + internal ALBs or later moves REST/Haystack to ECS (Neo4j/RDS stay in the data subnets either way).
11. Academy budget vs two internal ALBs — collapse to one internal ALB with two TGs only if credits force it.
12. Academy budget vs `asg-neo4j`: keep the dedicated data-subnet ASG by default. Only fall back to a Haystack sidecar if credits force it — **RDS still stays in the data subnet group**.
13. Paid only: Marketplace AMI from `prodview-a5jr6bo72f5aw` inside our data-subnet ASG, or stay on `neo4j:5`. Never the vendor CloudFormation stack.

---

## 13. Summary

The compose estate is a **small number of containers on one bridge network**. This Vocareum lab is **long-lived, credit-capped, and IAM-locked** (`LabRole` only), but it **does** allow ECS, Fargate, and EKS if you use the pre-created roles.

That still selects a **simple three-tier VPC**. **Academy (§6):** four **Auto Scaling groups** (portal / REST / Haystack in **private app** subnets; Neo4j in **private data** subnets), a **public ALB for the portal only**, dedicated **internal** ALBs for REST and Haystack, **one** single-AZ RDS and **one** Neo4j in the data subnet group (`LabRole`, no NAT Gateway, no Marketplace AMI). **Paid (§6P):** the same tiers in a **separate** account — Multi-AZ standby, second RDS, NAT Gateway, HTTPS, and an optional Marketplace AMI in *our* data-subnet ASG. REST, Haystack, RDS, and Neo4j are not internet-facing. **EKS is allowed and still the wrong default.**

**Two GitHub Actions pipelines** are the trigger:

- **CI** (app Release): **creates the Docker image**.
- **CD Academy** (`aws-infra-academy.yml`): same maintainer **Environment `academy` copy** → Terraform → **`sync-secrets`** → pull that image → Ansible. `stop` pauses; `destroy` runs `terraform destroy` on Academy state.
- **CD Paid** (`aws-infra-paid.yml`): same maintainer **Environment `paid` copy** + OIDC → Terraform → **`sync-secrets`** → pull that image → Ansible. `destroy` is paid state only.

EC2s never read GitHub. They retrieve **AWS Secrets Manager**. CD updates those AWS secrets from the GitHub Environment secrets the maintainer configured (and copied onto the CD repo).

Do **not** type keys on either form. Do **not** merge the two workflows. App Release only publishes images. OIDC is for paid only. Do not introduce **CDK** unless you drop Terraform.
