# EKS feasibility — recorded decisions

Design record only. Does **not** apply Terraform or change the live compose estate. Living specs: infra [`../../../heavy-rental-project-instructure-and-cloud-deploy/specification/`](../../../heavy-rental-project-instructure-and-cloud-deploy/specification/). Folder index: [`../README.md`](../README.md). Full argument: [`EKS-FEASIBILITY.md`](EKS-FEASIBILITY.md).

**Lab constraints used here:** Vocareum **`LabEksClusterRole`** for **cluster and node**. Instance types **nano, micro, small, medium, large**. Reference pipeline: `heavy-rental-project-instructure-and-cloud-deploy` (GitHub Actions trigger, Terraform creates architecture, Ansible configures what already exists).

---

## Recorded answers

### 1. Can the live cloud infrastructure pipeline spin up AWS EKS?

**No.** `aws-infra-academy.yml` / `aws-infra-paid.yml` + `terraform/academy/` create VPC + four ASGs + **`hr-bastion`** + ALBs + two RDS. There are no `aws_eks_*` resources. Infra README lists EKS as out of scope. Do not add `enable_eks` to the compose estate root (9-EC2 cap is **already full**; Ansible would still compose onto ASGs).

Details: [`EKS-FEASIBILITY.md`](EKS-FEASIBILITY.md) §2.

### 2. Can a **new** GitHub Action pipeline spin up EKS? Can Terraform and Ansible (same split as the infra repo) do it, with Actions as the trigger?

| Piece | Recorded decision |
| --- | --- |
| New GitHub Action | **Yes** — `aws-eks-academy.yml` (copy `workflow_dispatch`, `assert-lab`, Vocareum keys, S3 `use_lockfile`). New state key `eks/terraform.tfstate`. Not a flag on the live estate workflow |
| Terraform | **Yes — Terraform creates the cluster.** `aws_eks_cluster` + `aws_eks_node_group`. `role_arn` and `node_role_arn` both = data-source **`LabEksClusterRole`**. No `aws_iam_role` on Academy. Nodes `t3.nano`–`t3.large` |
| Ansible | **No for create.** Same contract as the estate: Ansible does not create VPC/ASG/RDS, and it does not `CreateCluster`. After nodes are Ready, `kubernetes.core` or `kubectl` may configure workloads. Do not reuse `configure.yml` / SSM `guest_base` |
| Paid | Second new Action. No `LabEksClusterRole` — Terraform **creates** cluster/node roles. OIDC, Environment `AWS_ACTUAL` |

Bar A (cluster + 2 nodes, `kubectl get nodes` Ready) is the minimum. Bar B (Heavy Rental apps on the cluster) is a later wave.

Details: [`EKS-FEASIBILITY.md`](EKS-FEASIBILITY.md) §2.1. Sketch: [`terraform-eks.example.tf`](terraform-eks.example.tf). Plan: [`IMPLEMENTATION-PLAN.md`](IMPLEMENTATION-PLAN.md).

### 3. Is the current EC2 + ALB + RDS architecture still applicable on EKS?

**Topology yes; four role ASGs no.** Reuse the underlay. Do not stack EKS on the live **9-guest** compose estate (`hr-bastion` already uses the last EC2 slot).

| Live building block | Recorded decision |
| --- | --- |
| VPC (public / app / data, two AZs, two NAT Gateways) | **Keep** |
| EC2 **role** ASGs (`asg-portal` / `asg-rest` / `asg-haystack` / `asg-neo4j`) + Compose | **Drop** — replaced by a managed node group + pods |
| EC2 as **worker nodes** | **Keep, different shape** — still EC2, nano–large, `LabEksClusterRole` |
| ALB / NLB graph (portal `:80`, REST `:8080` public, Haystack internal `:8000`, Bolt `:7687`) | **Keep the listeners.** Academy: Terraform ALBs + NodePort on the **node-group ASG**. Do not attach `tg-portal` to `asg-portal` |
| Two Multi-AZ RDS in data subnets | **Keep as-is.** Kubernetes does not replace Postgres. SG `:5432` from the node SG instead of `sg-rest` / `sg-haystack` |

Health paths stay: portal `GET /`, REST `GET /actuator/health` **2xx**, Haystack `GET /health` **2xx**.

Details: [`EKS-FEASIBILITY.md`](EKS-FEASIBILITY.md) §2.2.

---

## Files in this folder

| Path | Role |
| --- | --- |
| [`EKS-FEASIBILITY.md`](EKS-FEASIBILITY.md) | Full study (verdict, new Action, architecture mapping, IAM, cost, risks) |
| [`IMPLEMENTATION-PLAN.md`](IMPLEMENTATION-PLAN.md) | Gated delivery split **if** a rubric requires a cluster. Academy bar A first |
| [`terraform-eks.example.tf`](terraform-eks.example.tf) | Fail-closed Terraform sketch (`LabEksClusterRole`, nano–large). Not live |
| [`eks-infra-pipeline.example.yml`](eks-infra-pipeline.example.yml) | Fail-closed Academy Action stub (`exit 1`) |
| [`eks-infra-paid-pipeline.example.yml`](eks-infra-paid-pipeline.example.yml) | Fail-closed paid Action stub (`exit 1`) |

Example YAML is **not** live. Live compose estate stays in `heavy-rental-project-instructure-and-cloud-deploy`.
