# Implementation plan: EKS infra pipeline (gated)

## As-built (read this first)

**Do not start this plan** unless a course rubric requires Amazon EKS (or an explicit maintainer decision to stand up a **cluster**, bar A in [`EKS-FEASIBILITY.md`](EKS-FEASIBILITY.md) §2.1).

The live estate is four ASGs + **`hr-bastion`** + Ansible Compose (**9 EC2**, cap full). That path is **delivered** and stays the Heavy Rental default. This file is the delivery split for a **new** Action that creates EKS with **`LabEksClusterRole`** (cluster **and** node) and instance types **nano–large**. Do not stack it on the live compose estate.

| Contract | Where |
| --- | --- |
| Verdict | [`EKS-FEASIBILITY.md`](EKS-FEASIBILITY.md) |
| Live estate | `heavy-rental-project-instructure-and-cloud-deploy` (`terraform/academy/`, `aws-infra-*.yml`) |
| App CD (ASG) | `haystack-fast-api-pipeline/deploy-pipeline/`, `heavy-rental-rest-api/deploy-pipeline/`, `heavy-rental-web-portal-pipeline/deploy-pipeline/` |
| Isolation | Academy Vocareum vs Environment `AWS_ACTUAL` (infra ADRs 0017 / 0019) |

Conflict order if that repo uses OpenSpec: OpenSpec → OpenSPDD → ADR → YAML / Terraform / manifests.

**Status:** Study. No `terraform/eks/` tree exists. Example YAML in this folder stays fail-closed.

---

## 1. Goal (only if forced)

Stand up a **separate** EKS estate from GitHub Actions:

- **Bar A (this plan’s minimum):** `workflow_dispatch` `action=apply` creates an EKS cluster + managed node group. Academy: data-source **`LabEksClusterRole`** for **both** `role_arn` and `node_role_arn`. Nodes `t3.nano`–`t3.large`. `kubectl get nodes` Ready.
- **Bar B (later wave):** Secrets Manager + Kubernetes manifests (portal / REST / Haystack / Neo4j) from the runner (`kubectl` or Ansible `kubernetes.core` — **not** live `configure.yml`).
- Same communication graph as the live estate if bar B is done: portal public `:80`, REST internet-facing `:8080`, Haystack internal `:8000`, Bolt/RDS private.
- Same CI images. No `docker build` on nodes.
- `destroy` tears the cluster down. `stop` scales nodes to 0 and **prints that the control plane still bills**.

**Non-goals:**

- Adding `aws_eks_*` to `terraform/academy/`
- Adding an `eks` action to `aws-infra-academy.yml` / `aws-infra-paid.yml`
- Keeping the four compose ASGs in the same account while nodes exist (Academy 9-EC2 cap)
- Reusing Ansible `configure.yml` / `site.yml` / `guest_base` for pods
- CDK
- Marketplace Neo4j
- Academy IAM role **create** — data-source **`LabEksClusterRole` only**. Do not use `LabRole` / `LabInstanceProfile` for EKS
- Node instance types outside **nano, micro, small, medium, large**
- Mobile on the cluster

---

## 2. Where it lives

| Piece | Location |
| --- | --- |
| Workflows | `heavy-rental-project-instructure-and-cloud-deploy/.github/workflows/aws-eks-academy.yml` and `aws-eks-paid.yml` |
| Terraform | **New** `terraform/eks/` (not `terraform/academy/`) |
| State key | `eks/terraform.tfstate` (academy bucket vs `-actual` bucket) |
| Manifests (bar B) | `k8s/` and/or Ansible `kubernetes.core` from the runner. **Not** `guest_base` / SSM compose |
| App CD rewrite | Later wave in each app family’s `deploy-pipeline/` — `kubectl`, not `aws_ssm.py` |
| Auth | Same Environment names and secret **names** as live infra (`academy` Vocareum keys; `AWS_ACTUAL` OIDC) |

---

## 3. Prerequisites (fail closed)

Before branch 1 merge is allowed to `apply` anything:

1. [`EKS-FEASIBILITY.md`](EKS-FEASIBILITY.md) §13: `LabEksClusterRole` trust includes `eks.amazonaws.com` **and** `ec2.amazonaws.com`; Vocareum user can `PassRole` it; credits vs `$0.10`/h.
2. Live compose estate in that account is **destroyed** or never applied (Academy: do not hold 9 compose EC2 + nodes).
3. Academy: Terraform data-sources `LabEksClusterRole` only. Paid: OIDC role may create IAM (no `LabEksClusterRole` there).
4. Maintainer accepts that `action=stop` will **not** freeze EKS control-plane hours.

If (1) fails, **stop**. Do not write Terraform that cannot PassRole.

---

## 4. Order: Academy cluster first (LabEksClusterRole), then workloads, then paid, then app CD

```
Academy bar A: terraform/eks + LabEksClusterRole + 2× t3.medium
    → kubectl get nodes Ready
        → bar B: manifests / kubernetes.core (optional)
            → paid Action (create IAM; no LabEksClusterRole)
                → rewrite app CD callers (last)
```

Academy is the first customer **because this lab documents `LabEksClusterRole`**. Paid is a later file (different IAM). Do not burn lab credits on bar B until bar A `destroy` is proven.

### Why not 1 branch

| Count | Problem |
| --- | --- |
| **1** | Auth + VPC + cluster + LBC + RDS + manifests + app CD in one PR cannot be reviewed; a dead PassRole hides behind 15-minute creates |
| **3** | Smallest infra split: (1) Actions can plan an empty EKS root, (2) cluster+nodes exist, (3) workloads+secrets match the communication graph |
| **+1** | App CD rewrite is a **different repo tree** and must not block infra |

---

## 5. Branch 1 — `feat/infra-eks-skeleton`

**Purpose:** Actions authenticate and `terraform plan` against an **empty** `eks/` state key. No cluster.

### Tasks

1. OpenSpec change `add-infra-eks-pipeline` (scope: no compose ASGs, no estate state key, Ansible does not `CreateCluster`). ADR: “EKS is a separate root; Academy IAM is `LabEksClusterRole`.”
2. Copy the fail-closed examples → `aws-eks-academy.yml` / `aws-eks-paid.yml`.
3. Inputs: `action` (`plan` / `apply` / `kube-apply` / `stop` / `destroy`), `aws_environment`, `confirm_destroy`. Academy: three Vocareum keys. Paid: **no** key fields.
4. Jobs: `assert-lab` / `assert-account` (copy live patterns). Refuse Environment ≠ `academy` on the academy file; refuse `AWS_ACCESS_KEY_ID` on paid.
5. `terraform/eks/`: `versions.tf` (`hashicorp/aws ~> 5.0`, S3 backend key `eks/terraform.tfstate`, `use_lockfile=true`), empty `main.tf`, `variable "deployment"` `academy` \| `actual`.
6. `action=plan` inits the **eks** key and plans. Must not read `estate/terraform.tfstate`.
7. Concurrency group `aws-eks-academy-${{ github.repository }}` (not `aws-infra-academy-*`).

**Exit:** plan green, zero AWS EKS resources.

---

## 6. Branch 2 — `feat/infra-eks-cluster`

**Purpose:** `action=apply` creates a cluster and a node group. No Heavy Rental apps yet.

### Tasks

1. Academy: `data.aws_iam_role.lab_eks` name **`LabEksClusterRole`**. Plan **fails** if missing. **Both** `aws_eks_cluster.role_arn` and `aws_eks_node_group.node_role_arn` = that ARN. No `aws_iam_role`. No `LabInstanceProfile`. Sketch: [`terraform-eks.example.tf`](terraform-eks.example.tf).
2. Preflight job step: `aws iam get-role --role-name LabEksClusterRole` (parallel to live `LabRole` / `LabInstanceProfile` check).
3. VPC: either data-source a donated underlay **or** a small dedicated VPC (two AZs). Private nodes. NAT or public subnets for the cluster ENIs. Do not create the four compose ASGs.
4. `aws_eks_cluster` `us-east-1`, public endpoint (runner `kubectl`), access mode `API`, bootstrap creator admin.
5. `aws_eks_node_group` in private subnets. `instance_types` validated to **nano / micro / small / medium / large** (default `t3.medium`). desired **2**.
6. Outputs: `cluster_name`, `cluster_endpoint`, `node_group_name`, `lab_eks_cluster_role_arn`. No `asg_portal`.
7. Job step: `aws eks update-kubeconfig` + `kubectl get nodes`. Fail if nodes are `NotReady`.
8. `action=destroy` with `confirm_destroy=destroy`. Timeout ≥ 60 minutes.
9. `action=stop`: scale node group to 0; **echo that the control plane still bills**. Do not call `stop-estate.sh`.

Paid variant of this branch (later): `aws_iam_role` cluster + node + attachments. Do not data-source `LabEksClusterRole`.

**Exit:** `kubectl get nodes` shows Ready. No Deployments.

---

## 7. Branch 3 — `feat/infra-eks-workloads`

**Purpose:** Same runtime as compose, on the cluster.

### Tasks

1. Terraform: two Multi-AZ RDS in **data** subnets (or data-source them if donated), SM shells `heavy-rental/{portal,rest,haystack,neo4j}`.
2. `sync-secrets` adapted to EKS outputs (Ingress DNS, not ASG names). Same JSON fields as [`../AWS-INFRASTRUCTURE-FEASIBILITY.md`](../AWS-INFRASTRUCTURE-FEASIBILITY.md) §6.0c.
3. Paid: IRSA roles per app + External Secrets or CSI. Academy: node-role `get-secret-value` Job that materializes Kubernetes Secrets (document the isolation regression).
4. AWS Load Balancer Controller (paid IRSA; Academy only if **`LabEksClusterRole`** already has ELB APIs — otherwise fail the branch, do not open NodePorts to `0.0.0.0/0`).
5. Manifests: portal / REST / Haystack Deployments, Haystack workers, Neo4j StatefulSet. Health paths **unchanged**: REST `/actuator/health` **2xx**, Haystack `/health` **2xx`, portal `/` 200/301/302.
6. Ingress annotations: portal and REST internet-facing; Haystack `scheme=internal`; Neo4j internal NLB `:7687`.
7. `action=kube-apply`: `kubectl apply -k k8s/` **or** Ansible `kubernetes.core` from the **runner**. Not live `configure.yml` / SSM `guest_base`.
8. Resource requests from estate §6.4a. If Neo4j OOM, raise node desired (Academy cap 9, class `large`).

**Exit:** portal ALB serves the SPA; REST `:8080/actuator/health` 2xx; Haystack not public; RDS not public.

---

## 8. Later wave — app CD rewrite (do not block infra)

Only after branch 3 is accepted.

| Family | Replace | With |
| --- | --- | --- |
| Portal CD | discover `asg-portal` + Ansible `--limit portal` | `kubectl set image deploy/portal …` + verify Ingress |
| REST CD | `asg-rest` | `deploy/rest` |
| Haystack CD | `asg-haystack` | `deploy/haystack` (workers stay infra-owned unless they share the image) |

Callers stay split: `*-cd-academy-caller.yml` vs `*-cd-paid-caller.yml`. **No** Terraform. **No** Vocareum keys on paid. Fail if the cluster is missing.

Do **not** leave the old ASG discover jobs enabled against an EKS account — they will fail looking for `asg-haystack` or, worse, compose onto leftover guests.

---

## 9. Explicitly out of this plan

- Changing live `aws-infra-*.yml` job graphs except a README pointer
- `tls_private_key`, Marketplace AMIs, CDK
- EKS Auto Mode, Provisioned Control Plane tiers
- X-Ray / AMP / OpenSearch on Academy
- Putting RDS inside the cluster
- A Neo4j causal cluster

---

## 10. Rollback

The rollback is **do not merge**. The live compose pipeline stays the default. If an EKS root was applied: `action=destroy` on **`aws-eks-*` only**. Never `destroy` the compose estate by accident (different concurrency group, different state key, different workflow file).
