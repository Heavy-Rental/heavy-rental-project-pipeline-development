# Terraform in GitHub Actions (feasibility studies)

**Status:** Contract only. There is no live `.tf` in this folder. Infra example YAML `terraform` / `destroy` jobs are fail-closed stubs (`exit 1`).

**Sources:** [`AWS-INFRASTRUCTURE-FEASIBILITY.md`](AWS-INFRASTRUCTURE-FEASIBILITY.md) §7.0–§7.2d; [`aws-infra-pipeline.example.yml`](aws-infra-pipeline.example.yml); [`aws-infra-paid-pipeline.example.yml`](aws-infra-paid-pipeline.example.yml).

App CD (Haystack / REST / portal) **never** runs Terraform. Guest compose is [`ANSIBLE-PROCESS.md`](ANSIBLE-PROCESS.md).

---

## 1. Which workflow runs Terraform

Only **infra CD**:

| Workflow (copy name) | Environment | Auth |
| --- | --- | --- |
| `aws-infra-academy.yml` | `academy` | Vocareum three keys: **Run-workflow form** (they change every Start Lab) or Environment fallback. **Not paid.** |
| `aws-infra-paid.yml` | `paid` | OIDC `vars.AWS_ROLE_TO_ASSUME` (`id-token: write`) |

Trigger: **`workflow_dispatch` only**. Form fields: `action`, `aws_environment`, `confirm_destroy` when wiping, and on **Academy only** the three Vocareum keys (optional if Environment `academy` is set). **Paid has no key fields.**

Academy: **Start Lab** then paste AWS Details on the form. If `sts` fails (`ExpiredToken`), paste a fresh token. Do not apply on a dead session.

---

## 2. When the Terraform job runs

| `action` | Terraform? | Commands on the runner |
| --- | --- | --- |
| `plan` | Job `terraform` | `init` → `plan` |
| `apply` | Job `terraform` | `init` → `plan` → `apply` |
| `destroy` | Job **`destroy`** (not the plan/apply job) | `confirm_destroy == destroy` → `init` → `destroy -auto-approve` |
| `configure-only` | **Skipped** | `sync-secrets` + `sync-ssh-keys` + Ansible only |
| `stop` | **Skipped** | AWS CLI: ASG desired=0 + `rds stop-db-instance` (not `terraform destroy`) |

Do **not** `apply` on push or pull_request. A later optional `plan` on a trusted branch is out of the stub.

Timeouts in the examples: plan/apply **30** minutes; destroy **60** minutes (RDS + ALB delete is slow).

---

## 3. Steps inside the Actions `terraform` job (`plan` / `apply`)

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
        │
        ▼
  Terraform outputs (ALB DNS, RDS endpoint, Neo4j private IP, secret ARNs)
        │
        ▼
  Not Terraform — later jobs on apply only:
     sync-secrets      put-secret-value from outputs + GitHub Environment app secrets
     sync-ssh-keys     wait InService; PEMs  (no tls_private_key in .tf)
     ansible           guest compose  (see ANSIBLE-PROCESS.md)
```

`configure-aws-credentials` and `checkout` are **Actions** steps. `init` / `plan` / `apply` are the **Terraform** process.

`sync-secrets` is **not** Terraform. It reads `terraform output` (or the AWS API) and writes Secrets Manager. Terraform only created the **empty secret shells**.

---

## 4. Steps inside the Actions `destroy` job

```
assert-lab / assert-account
        │
        ▼
confirm_destroy == "destroy"         else fail; do not init
        │
        ▼
Job destroy
  1. configure-aws-credentials       same Environment / same account as apply
  2. checkout
  3. terraform init                  same backend + same state key as apply
  4. terraform destroy -auto-approve
```

No Ansible. No `stop` first. Same state key as that pipeline’s `apply`. Academy destroy never touches paid state.

Details of what is deleted: AWS study **§7.2d**.

---

## 5. Remote state (required because the runner is ephemeral)

A local `terraform.tfstate` on `ubuntu-latest` is gone when the job ends. The next `apply`/`destroy` would orphan the VPC or fail.

| Rule | Why |
| --- | --- |
| `terraform init` uses **S3 + DynamoDB lock** | State survives the job; lock stops two applies |
| Academy key ≠ paid key | One run must never see the other estate |
| Backend **bucket** is not in this state | Chicken-and-egg; `destroy` empties the state object, not the bucket |
| Vocareum **Reset** deletes the bucket | Keep `.tf` in Git; re-`apply` |

Local state is CloudShell / laptop **break-glass** only.

Exact bucket and key names are **other project**. Actions only needs them in the backend block (or `-backend-config`).

---

## 6. What Terraform puts in that state

| In state (Terraform creates) | Not in Terraform |
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

---

## 7. Outputs the later jobs need

`sync-secrets` builds JSON from Terraform outputs + GitHub Environment secrets:

| Output | Lands in |
| --- | --- |
| Internal REST ALB DNS | `heavy-rental/portal` → `REST_BASE_URL` |
| Internal Haystack ALB DNS | `heavy-rental/rest` → `HAYSTACK_URL` |
| RDS endpoint hostname + port | `heavy-rental/rest` and `heavy-rental/haystack` → `POSTGRES_HOST` / `_PORT` / URL |
| `asg-neo4j` private IP | `heavy-rental/haystack` → `NEO4J_URI` (`bolt://…:7687`) |

Do not echo SecretString, `sk_`, or PEMs in the job log or step summary. Public portal ALB DNS may be printed.

---

## 8. Academy rules inside `.tf`

- **No** `aws_iam_role` / OIDC provider. Data-source `LabRole` / `LabInstanceProfile` on every ASG, including `asg-neo4j`.
- `region = us-east-1`.
- No `aws_nat_gateway`. No Marketplace Neo4j AMI / vendor CFT.
- RDS class ≤ medium; data subnet group only; no enhanced monitoring.
- `asg-neo4j`: `max_size = 1`, EC2 health only, scale-in protection.
- Never register REST or Haystack on the public listener.
- Never a lone `aws_instance` outside an ASG (NAT instance is the documented exception).

Paid may add IAM instance profiles, Multi-AZ, NAT Gateway, ACM HTTPS, a second RDS — **different state**, same three tiers.

---

## 9. Terraform / Actions must not

- Run Terraform from Haystack / REST / portal **app CD**
- `apply` when `assert-lab` failed or the session token expired
- Put AWS keys on `workflow_dispatch`
- Mix CDK apply with this state
- Use local state on the GitHub runner
- `destroy` unless `confirm_destroy` is the literal string `destroy`
- Recreate RDS on every image deploy (`configure-only` + Ansible)
- Write PEMs or Stripe secrets into `.tf` or Terraform state (`tls_private_key` is forbidden)

---

## 10. Pointers

- Estate: [`AWS-INFRASTRUCTURE-FEASIBILITY.md`](AWS-INFRASTRUCTURE-FEASIBILITY.md) §7.1, §7.2a job graph, §7.2d destroy
- Guest after apply: [`ANSIBLE-PROCESS.md`](ANSIBLE-PROCESS.md)
- Example workflows: [`aws-infra-pipeline.example.yml`](aws-infra-pipeline.example.yml), [`aws-infra-paid-pipeline.example.yml`](aws-infra-paid-pipeline.example.yml)
