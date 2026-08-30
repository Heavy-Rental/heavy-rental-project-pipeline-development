# Feasibility study: can the cloud infrastructure pipeline spin up AWS EKS?

## As-built (read this first)

This file is a **design record**. It does **not** apply Terraform, create an EKS cluster, or change the live estate. Living specs win:

- Estate (compose-on-EC2): [`../../../heavy-rental-project-instructure-and-cloud-deploy/specification/`](../../../heavy-rental-project-instructure-and-cloud-deploy/specification/)
- App CI + CD families: [`../../specification/`](../../specification/)
- Parent index: [`../README.md`](../README.md)
- Compact recorded answers: [`README.md`](README.md)
- Original estate study Option B: [`../AWS-INFRASTRUCTURE-FEASIBILITY.md`](../AWS-INFRASTRUCTURE-FEASIBILITY.md) §5.B

| Topic | Live estate (as-built) | This EKS study |
| --- | --- | --- |
| Compute | Four ASGs (`asg-portal` / `asg-rest` / `asg-haystack` / `asg-neo4j`) + Docker Compose + single **`hr-bastion`** (9 EC2, cap full) | Would **replace** those ASGs (and the bastion) with an EKS node group. Not additive |
| Academy IAM (EC2) | Data-source `LabRole` / `LabInstanceProfile` (ADR 0005) | EKS uses pre-created **`LabEksClusterRole` for cluster *and* node**. Still **no** `aws_iam_role` resources |
| Node / guest class | `t3.micro`–`t3.large` | **nano, micro, small, medium, large only** (Vocareum). Cap at `t3.large` |
| Infra Actions | `aws-infra-academy.yml` + `aws-infra-paid.yml` | **Cannot** create EKS today. A **new** Action **can** (`aws-eks-academy.yml` + `terraform/eks/` + new state key) |
| Terraform root | `terraform/academy/` (`var.deployment` = `academy` \| `actual`) | No `aws_eks_*` in the live root. EKS Terraform is a **new** root, same CLI pin (1.15.8 / `hashicorp/aws ~> 5.0`) |
| Guest config | Ansible `configure.yml` / `site.yml` over SSM | Ansible **does not create** the cluster (same split as the estate). After apply, Ansible `kubernetes.core` *or* `kubectl` can configure workloads |
| App CD | Discover ASG → Ansible `--limit` one group | Would have to become `kubectl` / Helm. Current callers are useless against a cluster |
| `action=stop` | ASG desired=0 + stop both RDS | **Cannot** pause the EKS control plane. Scale-to-zero nodes still bills `$0.10`/cluster-hour |
| Paid Environment | `AWS_ACTUAL` | Same name if a paid EKS Action is ever written. Paid has **no** `LabEksClusterRole` — Terraform **creates** cluster/node roles |
| REST ALB | Internet-facing `:8080` (ADR 0018) | **Keep the listener.** Academy: Terraform ALB + NodePort on the node-group ASG. Do not attach `tg-rest` to `asg-rest` |
| VPC + two RDS | Three tiers; SoR + Haystack in data subnets | **Keep.** Kubernetes does not replace Postgres |

**Status:** Study only. Example YAML in this folder is **fail-closed**. Do not copy it into `.github/workflows`.

**Destinations (same two accounts as the estate study):**

1. **Academy** — AWS Academy Learner Lab (Vocareum). IAM-locked. Credit-capped.
2. **Paid** — billed commercial AWS account. Full IAM. GitHub OIDC.

One run must never touch the other. EKS does not change that isolation.

**Sources:** live `heavy-rental-project-instructure-and-cloud-deploy` (`aws-infra-academy.yml`, `terraform/academy/`, ADR 0005); estate study §3 / §5.B / §7; Vocareum Learner Lab: EKS **`LabEksClusterRole`** for **cluster and node**, instance types **nano–large**; [Amazon EKS pricing](https://aws.amazon.com/eks/pricing/) (standard support **`$0.10` per cluster per hour**). Re-read the Vocareum Readme if the lab image republishes the role name.

---

## 1. Purpose and non-goals

### Purpose

Answer the operator questions:

> Can the **existing** cloud infrastructure pipeline (`aws-infra-academy.yml` / `aws-infra-paid.yml`) spin up Amazon EKS?

> Can a **new** GitHub Action pipeline, using the same Terraform + Ansible *split* as `heavy-rental-project-instructure-and-cloud-deploy`, spin up Amazon EKS? Academy IAM is pre-created **`LabEksClusterRole`** (cluster **and** node). Node instance types are **nano, micro, small, medium, large**.

Break that into:

1. **As-is reuse** — flip live `action=apply` and get a cluster.
2. **New Action** — copy the live trigger (`workflow_dispatch`, `assert-lab`, Vocareum keys, S3 state) onto **new** files that apply `terraform/eks/`.
3. **Terraform vs Ansible** — same contract as the estate: Terraform **creates** AWS architecture; Ansible only **configures** what already exists.
4. **LabEksClusterRole** — data-source only (ADR 0005 analogue). Never `aws_iam_role`.
5. **Academy vs paid** — Vocareum vs a billed account.
6. **Current architecture** — is the live **EC2 + ALB + RDS** topology still the right shape under EKS? (**§2.2**)

### Non-goals

- Implementing live `aws_eks_cluster` / node groups / Helm charts
- Changing the recommended estate (still four ASGs + `hr-bastion` + Compose — estate study §2 / §5.A)
- Putting the Android APK on Kubernetes
- Mixing CDK with Terraform
- Running EKS **and** the eight-guest compose estate in the same Vocareum account (EC2 cap + credits)

Infrastructure, deploy, and operate of any future EKS estate would still belong to **`heavy-rental-project-instructure-and-cloud-deploy`**. This file is the decision record.

---

## 2. Verdict

| Question | Answer |
| --- | --- |
| Can the **live** infra pipeline (`aws-infra-*.yml`) spin up EKS today? | **No.** `action=apply` creates VPC + four ASGs + `hr-bastion` + ALBs + two RDS + secret shells. There is no EKS resource. Infra README lists EKS as out of scope. |
| Can we add `enable_eks=true` to `terraform/academy/`? | **No.** Same state as the compose estate. Academy would try to keep **9 compose EC2 plus nodes** (Vocareum cap **9**). Ansible would still compose onto ASGs that should not exist. |
| Can a **new** GitHub Action pipeline spin up EKS? | **Yes — cluster + managed node group.** Copy the live trigger (`workflow_dispatch`, `assert-lab`, Vocareum keys / OIDC, S3 `use_lockfile`, `plan` / `apply` / `destroy`). New files: `aws-eks-academy.yml` + `terraform/eks/` + state key `eks/terraform.tfstate`. See **§2.1**. |
| Terraform, with Actions as the trigger? | **Yes. Terraform is what creates the cluster.** Same split as the estate spec: Terraform owns AWS architecture. `hashicorp/aws ~> 5.0` already has `aws_eks_cluster` and `aws_eks_node_group`. |
| Ansible, with Actions as the trigger? | **Not to create EKS.** Same contract as [`infra-academy.md`](../../../heavy-rental-project-instructure-and-cloud-deploy/specification/pipelines/infra-academy.md): Ansible does **not** create VPC/ASG/RDS — and it does **not** `CreateCluster`. After Terraform, Ansible `kubernetes.core` (or `kubectl`) may configure workloads on the cluster that already exists. Do **not** SSM-compose onto node EC2. |
| Academy IAM: `LabEksClusterRole` for cluster **and** node? | **Yes — data-source only.** Parallel to ADR 0005 (`LabRole` / `LabInstanceProfile`). Plan fails if the role is missing. Terraform **never** `aws_iam_role`. Both `role_arn` (cluster) and `node_role_arn` (node group) = that ARN. |
| Instance types nano–large? | **Yes.** Pin `instance_types` to `t3.nano`–`t3.large` (default `t3.medium` or `t3.large`). Validation fails on `xlarge` / `r*` / Marketplace. Nodes count toward the **9 EC2** cap. |
| Paid (`AWS_ACTUAL`)? | **Yes, as a second new Action.** No `LabEksClusterRole` — Terraform **creates** cluster/node (and later IRSA) roles. OIDC. Separate state suffix `-actual`. |
| Reuse live Ansible `configure.yml` / `site.yml` / `guest_base`? | **No.** Those plays install Docker and `compose up` on named ASG guests over SSM. |
| Reuse portal / REST / Haystack app CD? | **No.** They discover `asg-*`. A cluster needs `kubectl set image` / Helm. |
| Reuse CI Release images? | **Yes.** Same GHCR/ECR tags. CD still must not `docker build`. |
| Is the live **EC2 + ALB + RDS** architecture still applicable on EKS? | **Topology yes; role-ASGs no.** Keep the VPC tiers, the four listeners (portal `:80`, REST `:8080`, Haystack internal `:8000`, Bolt NLB), and **both RDS**. Replace `asg-portal` / `asg-rest` / `asg-haystack` / `asg-neo4j` (and `hr-bastion`) with a node group + pods. Do not stack EKS on the live **9-guest** compose estate. See **§2.2**. |

**One line:** a **new** GitHub Action can spin up EKS; Terraform creates it (data-source `LabEksClusterRole`); Ansible does not create it; the **live** estate pipeline stays compose-on-EC2.

---

## 2.1 New GitHub Action pipeline (LabEksClusterRole)

This is the path that **works**, using the infra repo as the reference — not a flag on `aws-infra-academy.yml`.

### Trigger (copy the live Action)

Live Academy CD ([`aws-infra-academy.yml`](../../../heavy-rental-project-instructure-and-cloud-deploy/.github/workflows/aws-infra-academy.yml)):

```
workflow_dispatch
  → refuse-non-academy
  → assert-lab          resolve-aws-profile + sts (Vocareum three keys)
  → ensure-backend      terraform/backend S3 use_lockfile
  → terraform           init / plan / apply   terraform/academy/
  → sync-secrets        (not Terraform)
  → Ansible             configure.yml on guests Terraform already created
```

A new EKS Action is the **same graph** with a different working directory and no ASG Ansible:

```
workflow_dispatch          NEW  aws-eks-academy.yml
  → refuse-non-academy
  → assert-lab             SAME composite (Vocareum keys, Environment academy)
  → ensure-backend         SAME bucket; DIFFERENT object key
  → preflight              get-role LabEksClusterRole  (not LabInstanceProfile)
  → terraform              NEW  terraform/eks/   creates cluster + node group
  → kube-apply (later)     kubectl or Ansible kubernetes.core against the API
```

| Live piece to copy | EKS Action |
| --- | --- |
| `on: workflow_dispatch` + `action` choice | `plan` / `apply` / `stop` / `destroy` (add `kube-apply` later) |
| Environment `academy` | Same. Paid is a **second** file + `AWS_ACTUAL` |
| `.github/actions/resolve-aws-profile` + Vocareum form keys | Same. Keys stay on the **runner**. Never in SM, never on nodes |
| `hashicorp/setup-terraform` **1.15.8** | Same |
| S3 backend `use_lockfile=true` | Same **bucket** `heavy-rental-tfstate-<account>-academy`. Key **`eks/terraform.tfstate`** — never `estate/terraform.tfstate` |
| Concurrency group | **`aws-eks-academy-${{ github.repository }}`** — must not share the estate lock |
| Apply timeout | Cluster create is 10–15 min; node group another 5–10. **≥ 45 min** (live estate terraform job is already 90) |
| `confirm_destroy=destroy` | Same fail-closed destroy |
| Preflight | `aws iam get-role --role-name LabEksClusterRole` (estate preflight is `LabRole` + `LabInstanceProfile`) |

Do **not** add an `eks` option to the live estate workflow. Separate files, separate state, separate concurrency — same isolation rule as ADR 0019 (academy vs paid).

### Terraform creates the cluster (Ansible does not)

Estate contract ([`infra-academy.md`](../../../heavy-rental-project-instructure-and-cloud-deploy/specification/pipelines/infra-academy.md)):

| Tool | Owns |
| --- | --- |
| **Terraform** | Architecture and cloud **resources** |
| **Ansible** | Guest **configuration** only. **No** `terraform apply`, no create-ASG, no create-RDS |

EKS must keep that split:

| Tool | Creates EKS cluster / node group? | What it may do |
| --- | --- | --- |
| GitHub Actions | No (orchestrator) | `workflow_dispatch` → credentials → `terraform apply` → optional kube apply |
| **Terraform** `terraform/eks/` | **Yes** | VPC (or data-source), `aws_eks_cluster`, `aws_eks_node_group`, SGs, outputs |
| **Ansible** | **No** | After nodes are Ready: `kubernetes.core.k8s` / Helm from the **runner** (cluster API). Not `community.aws.eks_cluster`. Not SSM Docker on node EC2 |
| AWS CLI on the runner | Only as a helper | Preflight `get-role`, `aws eks update-kubeconfig`. Not the source of truth for the cluster |

Using Ansible to `aws eks create-cluster` would break the reference repo on purpose. Using Ansible `guest_base` + compose on node instances would fight the kubelet the node group already installed.

### LabEksClusterRole (Academy) — data-source, both ARNs

Vocareum pre-creates **`LabEksClusterRole`** for **cluster and node**. Terraform does not create IAM (ADR 0005 analogue). `LabRole` / `LabInstanceProfile` stay on the **compose** estate; they are the wrong pairing for EKS.

Sketch (full file: [`terraform-eks.example.tf`](terraform-eks.example.tf)):

```hcl
data "aws_iam_role" "lab_eks" {
  name = var.lab_eks_cluster_role_name # default LabEksClusterRole

  lifecycle {
    postcondition {
      condition     = self.name == "LabEksClusterRole"
      error_message = "Academy EKS must data-source LabEksClusterRole. Do not create IAM."
    }
  }
}

resource "aws_eks_cluster" "this" {
  name     = "hr-eks-academy"
  role_arn = data.aws_iam_role.lab_eks.arn   # cluster
  vpc_config {
    subnet_ids              = aws_subnet.eks[*].id
    endpoint_public_access  = true  # GitHub-hosted runner kubectl
    endpoint_private_access = true
  }
  access_config {
    authentication_mode                         = "API"
    bootstrap_cluster_creator_admin_permissions = true
  }
}

resource "aws_eks_node_group" "this" {
  cluster_name    = aws_eks_cluster.this.name
  node_group_name = "hr-eks-nodes"
  node_role_arn   = data.aws_iam_role.lab_eks.arn   # node — same role
  subnet_ids      = aws_subnet.eks_private[*].id
  instance_types  = [var.node_instance_type]        # t3.nano … t3.large
  scaling_config {
    desired_size = 2
    min_size     = 1
    max_size     = 2
  }
}
```

| Rule | Why |
| --- | --- |
| One pre-created role for **both** ARNs | Vocareum: cluster **and** node use `LabEksClusterRole` |
| No `aws_iam_role` / `aws_iam_instance_profile` | Academy cannot create IAM. The managed node group / EKS nodegroup SLR wraps the role |
| No `LabInstanceProfile` on the node group | That profile is for compose ASGs (`LabRole`). Wrong trust for kubelet |
| Preflight `get-role LabEksClusterRole` | Same idea as the live job’s `LabRole` / `LabInstanceProfile` check |
| `iam:PassRole` of that role to `eks.amazonaws.com` | The Vocareum **user** (Actions runner keys) must be able to pass it — same as the console “pick LabEksClusterRole” path |
| Trust must include `eks.amazonaws.com` **and** `ec2.amazonaws.com` | Cluster service + worker EC2. If Vocareum’s role is missing one, apply dies — **do not** `update-assume-role-policy` (that is IAM write) |

Plan-time proof (Actions step, next to the live LabRole preflight):

```bash
aws iam get-role --role-name LabEksClusterRole \
  --query 'Role.{Arn:Arn,Trust:AssumeRolePolicyDocument}'
# Fail if the role is missing.
```

### Instance types (nano–large)

| Allowed | Not allowed |
| --- | --- |
| `t3.nano`, `t3.micro`, `t3.small`, `t3.medium`, `t3.large` (and `t2.*` / `t3a.*` of those sizes if the lab lists them) | `xlarge` and above, `m5.xlarge`, `r*`, GPU, Marketplace |

Terraform validation:

```hcl
variable "node_instance_type" {
  type    = string
  default = "t3.medium"
  validation {
    condition     = can(regex("^(t[23]a?\\.(nano|micro|small|medium|large))$", var.node_instance_type))
    error_message = "Academy EKS nodes must be nano, micro, small, medium, or large."
  }
}
```

Nodes **are** customer EC2 and count toward Vocareum **≤ 9 instances**. The live compose estate already uses all 9 (`hr-bastion` is the last slot). **Do not** apply this pipeline while the 9-guest compose estate is running.

Checkbox cluster (prove the Action): `t3.medium` × 2. Full Heavy Rental in-cluster (Neo4j + three apps) still wants `t3.large` × 3–4 and is a **later** wave — see §6.2.

### What “spin up EKS” means (two bars)

| Bar | New Action + Terraform | Ansible |
| --- | --- | --- |
| **A. Cluster exists** — `kubectl get nodes` Ready | **Yes.** This is what LabEksClusterRole + nano–large unlock | Not required |
| **B. Heavy Rental apps on the cluster** | Underlay + cluster only | New plays (`kubernetes.core`) or `kubectl apply`. Live `configure.yml` / `site.yml` **cannot** |

Bar A is feasible on Academy with a new pipeline. Bar B is feasible on **paid** with IRSA; on Academy it inherits every pod sharing `LabEksClusterRole` (no IRSA) plus control-plane hours `stop` cannot pause.

### Paid new Action (no LabEksClusterRole)

`aws-eks-paid.yml` copies `aws-infra-paid.yml`: OIDC, Environment `AWS_ACTUAL`, **no** Vocareum key inputs. Terraform **creates** `hr-eks-cluster` and `hr-eks-node` roles (the live paid estate already creates `hr-paid-*` instance profiles — same permission, different names). Do not data-source `LabEksClusterRole` on paid; it will not exist.

---

## 2.2 Is the live EC2 + ALB + RDS architecture still applicable?

**Yes for the shape (VPC + listeners + two RDS). No for the four role ASGs.** EKS does not replace the Heavy Rental *communication graph*; it replaces *where the containers run*.

Live layout ([`ARCHITECTURE.md`](../../../heavy-rental-project-instructure-and-cloud-deploy/docs/ARCHITECTURE.md)):

```
public     ALB portal :80  +  ALB REST :8080  +  2 NAT GW
app        asg-portal / asg-rest / asg-haystack  +  internal Haystack ALB
data       asg-neo4j  +  Bolt NLB :7687  +  RDS SoR  +  RDS Haystack
```

| Live building block | Applicable on EKS? | What changes |
| --- | --- | --- |
| **VPC** three tiers, two AZs, IGW, two NAT Gateways, CIDRs `10.0.0.0/16` | **Yes — keep.** EKS needs two AZs of subnets. Same-AZ NAT still egress for image pull | Tag public subnets `kubernetes.io/role/elb=1`, private `kubernetes.io/role/internal-elb=1` if using the Load Balancer Controller. Cluster ENIs in at least two subnets |
| **EC2 role ASGs** `asg-portal` / `asg-rest` / `asg-haystack` / `asg-neo4j` + Docker Compose + **`hr-bastion`** | **No.** Those guests go away | One (or two) **managed node group(s)** — still EC2, class nano–**large**, `LabEksClusterRole`. Pods replace compose. Do **not** keep the four ASGs or the bastion (Vocareum cap **9**) |
| **EC2 as worker nodes** | **Yes.** EKS on this lab *is* EC2 (managed node group). Not Fargate-by-default | Nodes are anonymous kubelets, not `Role=portal`. Desired=2 for bar A; 3–4× `t3.large` if Neo4j is in-cluster |
| **ALB / NLB listeners** (portal public `:80`, REST internet-facing `:8080`, Haystack internal `:8000`, Bolt NLB `:7687`) | **Yes — keep the graph.** ADR 0018 still applies (REST ALB public; guests/pods not) | **Do not** keep `tg-*` attached to `asg-portal` etc. See ALB options below |
| **RDS** two Multi-AZ Postgres in **data** subnets, `publicly_accessible=false` | **Yes — keep as-is.** Kubernetes does **not** become Postgres | SG source is no longer `sg-rest` / `sg-haystack` instance SGs. Allow `:5432` from the **node** SG (Academy) or a pod SG (paid CNI). Same identifiers, same passwords, same `sync-secrets` JSON fields |
| Secrets Manager / ECR / observe | **Yes** | Same shells. Node/IRSA reads them, not Ansible `.env` on a named guest |

Do **not** run live 9 compose EC2 **and** EKS nodes in one account. The architecture is *reused as underlay*, not *stacked*.

### EC2

| Keep | Drop |
| --- | --- |
| EC2 **exists** as EKS worker nodes (`t3.nano`–`t3.large`) | `aws_launch_template` + `aws_autoscaling_group` per app role |
| Two AZs, private app subnets, no public IP on workers | `health_check_type = EC2` on `asg-portal` (ADR 0008) — kubelet + Deployment probes replace it |
| Neo4j as **derived** state (rebuild from SoR) | `asg-neo4j` Compose + extra EBS as the default. Prefer StatefulSet + PVC, or accept a second node group — **not** a leftover compose ASG next to EKS |

Worker nodes still count as EC2 toward the lab cap. That is why this is “EC2 + EKS”, not “EC2 *or* EKS”: the *role* ASGs are gone; *some* EC2 remains.

### ALB (and Bolt NLB)

The **listeners and schemes** stay the Heavy Rental contract. The **target** changes.

```
Browser → portal ALB :80     →  portal pods
       → REST ALB :8080      →  rest pods          (ADR 0018, still public ALB)
REST     → Haystack ALB :8000 →  haystack pods      (still internal)
Haystack → Bolt NLB :7687    →  neo4j pods          (still internal)
         → RDS :5432         →  same two instances
```

Health **paths** do not change: portal `GET /` 200–399, REST `GET /actuator/health` **2xx**, Haystack `GET /health` **2xx**, Bolt TCP 7687.

| Option | How | Academy | Faithfulness to `alb.tf` |
| --- | --- | --- | --- |
| **A. Terraform ALBs + NodePort** (recommended Academy) | Keep `hr-alb-portal` / `hr-alb-rest` / `hr-alb-haystack` / Bolt NLB. Target group **instance** mode registers the **node-group ASG** (EKS creates it). Services `type: NodePort`. ALB SG → node SG on the NodePort | **No extra IAM** (no LBC). Closest reuse of live `alb.tf` | High. DNS names can stay; `sync-secrets` barely changes |
| **B. Terraform ALBs + IP targets + LBC TargetGroupBinding** | Same ALBs; `target_type = ip`; controller registers pod IPs | Needs LBC IAM on `LabEksClusterRole` (unproven) | High DNS reuse; more moving parts |
| **C. Ingress creates ALBs** | Delete live `alb.tf`. Kubernetes Ingress annotations; LBC allocates new ALBs | Same IAM problem as B | Graph kept; **new** DNS — rewrite `REST_BASE_URL` / `HAYSTACK_BASE_URL` |

**Academy default: option A.** Paid may move to B/C once IRSA exists.

What **must not** stay: `aws_autoscaling_group.portal.target_group_arns = [tg-portal]` — there is no `asg-portal`.

### RDS

**Fully applicable.** Do not put `postgres-primary` / `postgres-haystack` in the cluster.

| Live RDS rule | On EKS |
| --- | --- |
| Two instances (`heavy-rental-academy`, `heavy-rental-haystack-academy`) | Same. Runner still cannot `CREATE DATABASE` on private RDS |
| `db_subnet_group` = **data** subnets only | Same |
| `multi_az = true`, class `db.t3.micro`, engine prefer 12.22 then 11.22 | Same |
| `sg-rds` `:5432` from app SGs only | From **node group SG** (and later a pod SG). Never `0.0.0.0/0` |
| `action=stop` stops both identifiers | **Still do this.** EKS does not stop RDS; the control plane is the extra bill |

`postgres-haystack-sync` stays a **worker** (Deployment/CronJob), not a third RDS.

### Side-by-side

```
LIVE (compose-on-EC2)                    EKS (same topology)
---------------------                    -------------------
public:  ALB portal, ALB REST, NAT ×2    SAME listeners + NAT
app:     3 role ASGs + internal ALB      node group (EC2) + same internal ALB
data:    asg-neo4j, Bolt NLB, 2× RDS     neo4j pods (or STS), SAME NLB, SAME 2× RDS
IAM:     LabRole / LabInstanceProfile    LabEksClusterRole (cluster + node)
```

**One line:** reuse VPC + ALB *graph* + RDS; replace role EC2 with an EKS node group; do not keep both compute styles.

---

## 3. What the live pipeline actually creates

This is the contract `action=apply` already ships. EKS has to beat or replace it, not sit beside it.

```
workflow_dispatch  aws-infra-academy.yml | aws-infra-paid.yml
        │
        ▼
assert-lab / assert-account     sts; refuse the wrong account
        │
        ▼
Terraform  terraform/academy/   VPC, 2 NAT GW, 4 ASGs, 3 ALBs, Bolt NLB,
                                2 Multi-AZ RDS, SM shells, ECR, observe
        │
        ▼
sync-secrets / sync-ssh-keys    fill SM JSON; PEMs after InService
        │
        ▼
Ansible configure.yml           Docker on every guest; Neo4j compose only
        │
        ▼  (later run)
Ansible site.yml                portal + REST + Haystack first-compose
        │
        ▼  (later, app repos)
App CD                          discover asg-* → compose one group
```

| Layer | Live owner | EKS equivalent |
| --- | --- | --- |
| Trigger | GitHub Actions `workflow_dispatch` | **Keep** (new workflow files) |
| Auth Academy | Vocareum three keys on the runner | **Keep** |
| Auth paid | OIDC `AWS_ROLE_TO_ASSUME` | **Keep**; widen the role for `eks:*` + `iam:PassRole` |
| State | S3 key `estate/terraform.tfstate` | **New** key. Do not store a cluster in the estate object |
| Network | `vpc.tf` + `nat.tf` three tiers | Reusable underlay **or** a dedicated VPC |
| Compute | `compute.tf` launch templates + ASGs | `aws_eks_cluster` + `aws_eks_node_group` (or Fargate profile) |
| Ingress | `alb.tf` instance target groups | Kubernetes Service/Ingress + AWS Load Balancer Controller (or in-tree ELB on older clusters) |
| Data | `rds.tf` + `asg-neo4j` + Bolt NLB | **RDS stays RDS.** Neo4j becomes a StatefulSet (or stays a data-subnet ASG — that wastes the point of EKS) |
| Secrets | SM shells + `sync-secrets` | Still fill SM. Pods need IRSA / CSI / a bootstrap Job — not Ansible `.env` on the guest |
| Configure | Ansible SSM | After the cluster exists: `kubectl` **or** Ansible `kubernetes.core` from the **runner**. Not SSM compose on nodes |
| Pause | `stop-estate.sh` | **Broken** for the control plane |
| Images | GHCR/ECR | **Keep** |

Pinned tooling (estate, 2026-08-17) is enough for EKS *resources*: Terraform **1.15.8**, `hashicorp/aws` `~> 5.0`. The provider is not the blocker. The **modules and the IAM story** are.

---

## 4. What Amazon EKS actually requires

Minimum to run the same three apps + Neo4j + two workers:

| Piece | Why | Academy | Paid |
| --- | --- | --- | --- |
| EKS cluster (control plane) | Kubernetes API | Allow-listed; **`$0.10`/hour**, cannot stop | Same price; can create IAM |
| Cluster IAM role | EKS service principal | **Cannot create.** Data-source **`LabEksClusterRole`**. `PassRole` to `eks.amazonaws.com` | Terraform `aws_iam_role` + `AmazonEKSClusterPolicy` (`LabEksClusterRole` does **not** exist here) |
| Node IAM role | Worker EC2 | **Same `LabEksClusterRole` ARN** as `node_role_arn`. Do not use `LabInstanceProfile` | Separate node role: `AmazonEKSWorkerNodePolicy` + `AmazonEKS_CNI_Policy` + `AmazonEC2ContainerRegistryReadOnly` |
| Worker nodes **or** Fargate | Place pods | **nano / micro / small / medium / large only**; count toward the **9 EC2** cap | Any class; cost is the limit |
| Two AZs of subnets | EKS + RDS already want this | Live VPC already has public / app / data pairs | Same |
| NAT or public nodes | Image pull, yum, EKS API from private nodes | Live estate already has **two NAT Gateways** (bill 24/7) | Same |
| Cluster access for the runner | `kubectl` from `ubuntu-latest` | Public cluster endpoint + IAM access entry for the Vocareum principal. Private-only API is unreachable from GitHub-hosted runners | Same unless you add a self-hosted runner (out of scope) |
| AWS Load Balancer Controller (modern EKS) | Portal / REST / Haystack / Bolt listeners | Needs IAM (IRSA **or** node `LabRole` if that role already has ELB APIs). **Cannot create** the controller role | Create IRSA role + policy |
| IRSA (OIDC provider + per-app roles) | Least-privilege pod AWS calls (SM, ECR) | **Forbidden** (no IAM roles, no OIDC provider). Pods share the **node** role — same accepted risk as all guests sharing `LabRole` today | **Do this** |
| EBS CSI (or equivalent) | Neo4j `/data` PVC | Same IAM story as LBC | Create CSI role |
| `kubectl`/Helm on the runner | Apply Deployments | Install in the job. Not an AWS service; Vocareum does not need to list it | Same |
| Add-on IAM (vpc-cni, CoreDNS, kube-proxy) | Cluster networking | vpc-cni wants `AmazonEKS_CNI_Policy` on the **node** role. Prefix-delegation / custom CNI role = extra IAM = Academy fail | Standard managed add-ons |

### 4.1 `LabEksClusterRole` (this lab)

**Given for this study:** Vocareum pre-creates **`LabEksClusterRole`**. Use it for **cluster and node**. Instance types **nano, micro, small, medium, large**.

Do **not** substitute `LabRole` / `LabInstanceProfile` (those are the compose estate pairing, ADR 0005). Do **not** create a second EKS role.

Before the first Academy `apply`, the new Action’s preflight (same style as live `get-role LabRole`):

```bash
aws iam get-role --role-name LabEksClusterRole \
  --query 'Role.{Arn:Arn,Trust:AssumeRolePolicyDocument}'
```

Plan **fails closed** unless:

1. `LabEksClusterRole` exists.
2. Trust allows `eks.amazonaws.com` (cluster) **and** `ec2.amazonaws.com` (nodes). If one is missing, stop — do not `update-assume-role-policy`.
3. The Vocareum user (Actions runner keys) can `iam:PassRole` that role to `eks.amazonaws.com`.
4. `var.node_instance_type` is nano–large.

Older public Learner Lab PDFs say EKS “can assume **LabRole**.” This lab image is **`LabEksClusterRole`**. If a future image drops the name, fix the data source — do not create IAM.

### 4.2 Why IRSA matters for this estate

Live isolation:

| Secret | Who may read it today |
| --- | --- |
| `heavy-rental/portal` | Academy: any guest (`LabRole`). Paid: `hr-paid-portal` only |
| `heavy-rental/rest` (`sk_`, RDS password) | Academy: convention. Paid: `hr-paid-rest` only |
| `heavy-rental/haystack` / `neo4j` | Same pattern |

On EKS without IRSA, **every pod on the node** can call `GetSecretValue` as the node role. Academy already accepted that for EC2. Paid **must not** — paid exists specifically to create `hr-paid-*`. An EKS paid cluster that skips IRSA would be a regression vs `iam.tf`.

---

## 5. Reuse matrix (the actual question)

| Live piece | Reuse as-is? | What would have to change |
| --- | --- | --- |
| Dual Actions (academy vs `AWS_ACTUAL`) | **Shape only** | New files `aws-eks-academy.yml` / `aws-eks-paid.yml`. Do **not** add an `eks` action to the live estate workflows |
| `workflow_dispatch` `action` = plan / apply / destroy | **Yes** | Add `kube-apply` (manifests) instead of `configure-only` / `deploy-projects`. `stop` becomes “scale node group to 0 + stop RDS” and **must warn** the control plane still bills |
| `assert-lab` / `assert-account` | **Yes** | Same sts / Environment checks |
| `terraform/backend/` S3 bucket | **Yes** | Second state **object**, same bucket is fine: `eks/terraform.tfstate` |
| `terraform/academy/vpc.tf` `nat.tf` `rds.tf` `secrets.tf` `ecr.tf` `observe.tf` | **Partial** | Copy or data-source into `terraform/eks/`. Do not `apply` them from two roots against the same resources |
| `compute.tf` four ASGs | **No** | Delete from the EKS design. Nodes ≠ `asg-portal` |
| `alb.tf` instance target groups | **Listeners yes; ASG attachments no** | Keep portal / REST / Haystack ALBs + Bolt NLB. Retarget the **node-group ASG** (NodePort, Academy) or pod IPs (LBC). Do not attach `tg-portal` to `asg-portal` |
| `iam.tf` `hr-paid-*` instance profiles | **No** (paid EKS) | Replace with cluster / node / IRSA roles. Profiles are for EC2 guests |
| ADR 0005 LabInstanceProfile-only | **Academy EKS still** | Data-source only. Never `aws_iam_role` on Academy |
| `scripts/sync-secrets.sh` | **Partial** | Still write SM JSON from Terraform outputs (RDS host, ALB/NLB DNS, Bolt URI). Outputs change (Ingress DNS, not `asg_*`) |
| `scripts/sync-ssh-keys.sh` | **No** | No guest PEM for pods. Break-glass is `kubectl exec` / SSM onto a **node**, not four ASG key pairs |
| `scripts/stop-estate.sh` | **No** | Hard-codes `asg-portal` … `asg-neo4j`. A new script would scale the **node group** and still cannot stop EKS |
| Ansible inventory `aws_ssm.py` groups | **No** | Inventory is Kubernetes, not four SSM groups |
| `guest_base` + compose templates | **No** | Become Deployment / StatefulSet / CronJob manifests. `mem_limit` / `cpus` become requests/limits |
| Haystack workers (`postgres:17` + `python:3.12-slim`) | **Images yes; placement no** | Same images as Deployments/CronJobs. Not sidecars on `asg-haystack` |
| App CD discover-ASG | **No** | Discover cluster name + namespace. Fail if the cluster is missing (operator runs EKS infra apply first) |
| CI Release GHCR tags | **Yes** | `image:` on the Deployment |
| Observe (CloudTrail, flow logs, ALB access logs) | **Partial** | Keep account-level trails. Add Container Insights / Control Plane logs only if the lab allow-list and budget say so. Estate study already forbids X-Ray / Managed Prometheus on Academy |
| Communication graph (portal public, REST `:8080` public, Haystack internal, Bolt/RDS private) | **Must keep** | Different mechanism, same SG contract |

---

## 6. Architecture if a rubric forced EKS

Not the recommended estate. Sketch only, so the reuse gaps are visible.

```
                         Internet
                             │
                      Internet Gateway
                             │
         ┌───────────────────┴──────────────────────────────────────────┐
         │                     VPC  (new EKS root, or donated underlay) │
         │  public AZ-0 / AZ-1                                          │
         │  NAT GW + EIP each; internet-facing ALBs (portal :80,        │
         │  REST :8080) created by AWS Load Balancer Controller         │
         │                  │                                           │
         │  private APP AZ-0 / AZ-1                                     │
         │  EKS nodes ×2 (t3.large, class cap on Academy)               │
         │    ns/heavy-rental                                           │
         │      deploy/portal      Service+Ingress  public :80          │
         │      deploy/rest        Service+Ingress  public :8080        │
         │      deploy/haystack    Service+Ingress  internal :8000      │
         │      deploy/sync        (no public port)                     │
         │      deploy/populate    (ClusterIP :8089)                    │
         │      sts/neo4j          Service internal NLB :7687           │
         │                  │ JDBC / Bolt                               │
         │  private DATA AZ-0 / AZ-1                                    │
         │  RDS SoR Multi-AZ + RDS Haystack Multi-AZ  (unchanged)       │
         └──────────────────────────────────────────────────────────────┘
```

Same three-tier idea as [`../AWS-INFRASTRUCTURE-FEASIBILITY.md`](../AWS-INFRASTRUCTURE-FEASIBILITY.md) §6 and **§2.2**. Kubernetes does **not** eat RDS or the ALB *graph*. It **does** eat the four role ASGs, Ansible SSM compose, and ASG-discover app CD. Academy ALBs stay Terraform-owned (NodePort → node-group ASG) unless LBC IAM is proven.

### 6.1 Options inside EKS (all still “if forced”)

| Option | Idea | Academy | Paid | Verdict |
| --- | --- | --- | --- | --- |
| **E1. Managed node group, private subnets** | Standard `aws_eks_node_group` in app subnets | 2× `t3.large` = 2 EC2 (under the cap **if ASGs are gone**). Node role = pre-created only | Create node role | Least-bad EKS shape |
| **E2. EKS + keep `asg-neo4j`** | Apps on nodes, graph still Compose | Extra EC2 + extra operate path (Ansible **and** kubectl) | Same mess | **Reject** — two compute styles |
| **E3. Fargate profiles** | No worker EC2 | Needs a **pod execution role**. Vocareum ECS text says LabRole as task+execution; EKS Fargate is a different API. Unproven | Create the role | Not the default; prove PassRole first |
| **E4. EKS Auto Mode** | AWS owns nodes | Extra IAM; likely blocked | Cost premium | Skip for this estate |
| **E5. Stack EKS on the live 9-EC2 compose VPC** | “Just add a cluster” | **9-EC2 cap already full** + double NAT/ALB/RDS spend + control plane | Double compute bill | **Reject** |

### 6.2 Workloads (manifest sketch)

| Compose / ASG role | Kubernetes object | Notes |
| --- | --- | --- |
| `asg-portal` nginx `:80` | Deployment + Service + Ingress (internet-facing) | `/api` still proxies to REST URL. Stripe `pk_` from SM |
| `asg-rest` Tomcat `:8080` | Deployment + Service + Ingress (internet-facing `:8080`) | Health: `GET /actuator/health` **2xx** (not `GET /`) |
| `asg-haystack` uvicorn `:8000` | Deployment + Service + Ingress (`scheme=internal`) | Health: `GET /health` **2xx**. Never public |
| `postgres-haystack-sync` | Deployment or CronJob | Same `postgres:17` + `sync-from-primary.sh`. `SOURCE_*` / `TARGET_*` from SM |
| `neo4j-populate` | Deployment (`:8089` ClusterIP) | Same `python:3.12-slim` + `populate-neo4j-from-haystack.sh` (wraps `populate_neo4j.py`) |
| `asg-neo4j` `neo4j:5` | StatefulSet + PVC + internal NLB Service | Not a causal cluster. Two replicas still independent |
| RDS SoR / Haystack | **Stay `aws_db_instance`** | Runner still cannot `CREATE DATABASE` on private RDS |

Resource requests should mirror estate §6.4a (`256m` portal, `1g` REST, `768m` uvicorn, `256m` workers, `4g` Neo4j). Two Academy `t3.large` nodes (**~8 GiB each**) **cannot** hold two Neo4j heaps plus three apps. Honest Academy node count is **3–4 × `t3.large`** if Neo4j is in-cluster — still ≤ 9, still tight, still plus control-plane hours.

### 6.3 Secrets on the cluster

| Path | Academy | Paid |
| --- | --- | --- |
| Init container `aws secretsmanager get-secret-value` using **node** role → write a Kubernetes Secret | Feasible (LabRole is already wide) | Regression — do not |
| External Secrets Operator / Secrets Store CSI + **IRSA** | No IAM role for the operator | **Do this** |
| Bake env into the image | Forbidden (Haystack ADR 0008, REST ADR 0007, portal ADR 0007) | Same |

`sync-secrets` remains the only writer into AWS Secrets Manager. Kubernetes is a **reader**.

---

## 7. Academy blockers (why “allowed” ≠ “the pipeline can”)

| Blocker | Detail | Live compose estate |
| --- | --- | --- |
| **IAM create** | No users/groups/roles except service-linked. IRSA, LBC role, CSI role, dedicated node role all die | Already designed around `LabRole` / `LabInstanceProfile` |
| **PassRole + trust** | Cluster create fails unless a pre-created role trusts `eks.amazonaws.com` and the lab user can pass it | EC2 instance profile is a known pairing; EKS is not proven in this lab image |
| **9 EC2 / 32 vCPU / class ≤ large** | Nodes count. Live estate already uses **9** (8 app + `hr-bastion`). Additive EKS is illegal. Replacement needs 3–4 `t3.large` for Neo4j+apps | 9 mixed `t3.micro/small/large` already fills the cap |
| **Control plane is always on** | `$0.10`/hour ≈ **`$2.40`/lab-day** ≈ **`$73`/month**, idle or not. Session end does **not** stop it. `action=stop` cannot. Only `destroy` | EC2 stop is free of instance-hours; RDS can be stopped |
| **NAT Gateways already 24/7** | Two Gateways + EIPs already accepted (ADR 0010). EKS does not remove them (private nodes still egress) | Same leak; EKS **adds** the control plane on top |
| **Public cluster endpoint** | GitHub-hosted runner must reach the API. `0.0.0.0/0` + IAM is the realistic Academy choice | Guests have no public IP; Ansible uses SSM instead |
| **Vocareum principal churn** | Cluster creator / access entry is a federated `voclabs/…` identity. Next Start Lab must still map | ASG names stay stable; SSM is instance-id based |
| **Modern ELB from Kubernetes** | In-tree `Service type=LoadBalancer` is going away. LBC wants IAM | Terraform already owns ALBs without Kubernetes |
| **`action=stop` contract** | Operators expect pause-for-credits. EKS breaks that expectation | `stop-estate.sh` is the lab-day path |
| **Operate/Monitor add-ons** | Estate study: no X-Ray, AMP, OpenSearch, EKS add-on monitoring on Academy | CloudWatch + `docker logs` over SSM |

**Budget sketch (order of magnitude, us-east-1, not a quote):** one cluster left up a 4-week class ≈ `$73` control plane **before** NAT (`~$65`/month for two Gateways), two Multi-AZ `db.t3.micro`, three ALBs, 3–4 `t3.large` nodes, and EBS. A `$50–$100` Learner Lab that already struggles with NAT+RDS will **disable the account**. Exceeding budget **deletes everything** (estate study §3).

### 7.1 What Academy EKS would still get right

If the rubric only needs “an EKS cluster exists”:

- `aws_eks_cluster` in `us-east-1` with `role_arn = data.aws_iam_role.<precreated>.arn`
- Two public or app subnets
- Public endpoint so the runner can `aws eks update-kubeconfig`
- **Zero or two** tiny nodes (`t3.micro`) and a `default` namespace `kubectl get ns`
- Destroy at the end of the demo hour

That is a **course checkbox**, not Heavy Rental. It does not carry portal/REST/Haystack/Neo4j, SM isolation, or app CD. Do not pretend it is the estate.

---

## 8. Paid (`AWS_ACTUAL`): feasible, still the wrong default

Paid **can** create every IAM object EKS wants. The live paid Action already:

- Assumes `vars.AWS_ROLE_TO_ASSUME` (OIDC)
- Creates `hr-paid-{portal,rest,haystack,neo4j}` instance profiles
- Uses a separate state suffix `-actual`

A paid EKS pipeline would **widen** that OIDC role (`eks:*`, `iam:CreateRole` / `PassRole`, OIDC provider) and **replace** instance profiles with cluster/node/IRSA roles.

| Paid extra (estate §6P) | EKS note |
| --- | --- |
| Create IAM | **Required** for a real cluster |
| HTTPS on portal ALB | ACM on the Ingress ALB; still not a class blocker |
| Larger instance classes | Nodes may be bigger than `large` |
| OIDC for GitHub | Already there; **add** the cluster OIDC provider for IRSA (different provider) |
| `action=stop` | Still cannot pause the control plane. Paid cost is money, not a wiped lab, but idle `$73`/month + NAT is waste |

**Do not** point `aws-infra-paid.yml` `action=apply` at EKS. That Action’s Ansible expects `asg-*` InService. A paid EKS apply that also creates those ASGs double-bills; one that does not will fail `configure.yml`.

---

## 9. Pipeline design if EKS is forced

Keep the **DevSecOps split**. CI still builds images. Infra CD still creates cloud resources. App CD still only rolls an image. EKS changes the **middle and the last**, not Release packaging.

```
CI  (unchanged)          docker build → GHCR / tar
        │
        ▼
EKS infra CD  (new)      terraform/eks apply
                         sync-secrets (RDS + Ingress DNS)
                         kubectl apply -k / helm upgrade  (first deploy)
        │
        ▼
App CD  (rewrite)        kubectl set image deploy/rest …   (no Terraform, no Ansible)
```

### 9.1 Actions (new files, same isolation)

| | Academy EKS | Paid EKS |
| --- | --- | --- |
| Workflow | `aws-eks-academy.yml` | `aws-eks-paid.yml` |
| Environment | `academy` | `AWS_ACTUAL` |
| Auth | Vocareum three keys | OIDC only; **fail** if `AWS_ACCESS_KEY_ID` is set |
| State key | `eks/terraform.tfstate` in `…-academy` bucket | same key in `…-actual` bucket |
| Terraform | Data-source pre-created EKS/Lab roles. **No** `aws_iam_role` | Create cluster/node/IRSA roles |
| After apply | `kubectl` from the runner, **not** Ansible SSM | Same |
| `stop` | Node group desired=0 + stop both RDS. Print: **control plane still bills** | Same |
| `destroy` | `confirm_destroy=destroy`. Deletes cluster, nodes, underlay this root owns | Paid state only |

Concurrency groups stay separate from `aws-infra-academy-*` so a compose-estate apply and an EKS experiment cannot share a lock and smash one state.

### 9.2 Terraform roots

```
terraform/
  backend/          # keep — bucket bootstrap
  academy/          # LIVE compose estate — do not add aws_eks_*
  eks/              # NEW — cluster, node group, (paid) IAM, optional donated VPC
```

`eks/` either:

- **Owns** a VPC + NAT + RDS + SM shells (cleanest isolation; duplicate cost), or
- **Data-sources** a pre-applied compose VPC (only after `destroy` of the four ASGs / `hr-bastion` / ALBs, otherwise the 9-EC2 cap and double ALBs).

Never two applies of the same `aws_vpc` from two states.

### 9.3 Timeouts

Cluster create is **10–15 minutes**. Destroy (ENIs, ALBs, node ASG) is often **15–20+**. Live estate apply timeout **30** / destroy **60** is in the right band; do not shrink it.

---

## 10. App CD would have to be rewritten

Live Haystack / REST / portal CD (see sibling folders) assume:

1. Infra already created `asg-<app>`
2. Guests are InService + SSM Online
3. Ansible `--limit <app>` composes the CI image
4. Verify hits instance or ALB health paths

On EKS those four bullets are wrong. A replacement CD:

| Step | Live | EKS |
| --- | --- | --- |
| Discover | `describe-auto-scaling-groups asg-haystack` | `describe-cluster` + `kubectl get deploy` |
| Fail closed | Missing ASG → “run infra apply” | Missing cluster / namespace → “run EKS infra apply” |
| Ship bits | `docker pull` / `docker load` on the guest | Cluster nodes pull GHCR/ECR. **Private GHCR still needs a pull secret or ECR copy** (same as today) |
| Auth on the workload | Instance profile `get-secret-value` | IRSA (paid) or node role (Academy) |
| Verify | SSM `GET :8000/health` **2xx** | `kubectl rollout status` + HTTP GET the **internal** Ingress/Service (runner may need `kubectl port-forward` if Haystack stays private) |

Do **not** keep Ansible SSM “because we already have it” and also run kubelets on the same instances. Pick one compute style.

Mobile stays unsigned APK / no VPC — unchanged.

---

## 11. Cost and complexity

| Design | Academy credits | Ops | Faithfulness to compose |
| --- | --- | --- | --- |
| **Live: 4 ASGs + ALBs + 2× RDS** (current) | Medium-high — `stop` pauses EC2/RDS; NAT still bills | Medium — Terraform + Ansible + SSM | High |
| EKS checkbox (cluster, 0–2 micro nodes, no apps) | Control plane `$0.10`/h until destroy | Low | None |
| EKS + in-cluster apps/Neo4j + 2× RDS | **Highest** — control plane + NAT + RDS + 3–4 `large` nodes; `stop` is a lie | Highest — IAM, LBC, PVCs, two CD styles if anyone leaves ASGs around | Medium (same images, different runtime) |
| ECS Fargate (estate Option C) | High; LabRole as task+execution | Medium | Medium |
| One public EC2 (estate Option D) | Lowest | Lowest | High and **wrong** (public APIs) |

Well-Architected (estate §6.8): Academy already trades reliability vs cost. EKS spends that cost budget on a control plane the class does not need. **Cost optimization and sustainability get worse**; operational excellence gets worse (more moving parts) unless the **rubric is Kubernetes**.

---

## 12. Risks

| Risk | Why it bites | Mitigation |
| --- | --- | --- |
| Feature-flag EKS in `terraform/academy/` | One state, 9 compose EC2 + nodes, Ansible on the wrong hosts | Separate root + state. Live estate stays EKS-free |
| Assume `LabEksClusterRole` exists | Lab image may only document `LabRole` | Data-source + plan fail; verify with `get-role` |
| `LabRole` trust is EC2-only | `CreateCluster` AccessDenied | Stop. Do not create IAM on Academy |
| IRSA on Academy | Forbidden | Accept node-role sharing **or** do not do Academy EKS |
| Idle control plane | Session end / `stop` leave `$0.10`/h + NAT | Destroy after the demo; never “leave the cluster up for next week” |
| Public kube-apiserver `0.0.0.0/0` | GitHub-hosted runner convenience | IAM auth still required; do not also open worker NodePorts to the internet |
| In-tree ELB gone on new Kubernetes | Academy cannot create LBC role | Prove LBC on `LabRole` **or** Terraform-owned ALBs with TargetGroupBinding (still needs LBC) |
| App CD left on ASG discover | Green workflows deploying nowhere | Gate: EKS app CD refuses if `asg-haystack` exists and no cluster does, and vice versa |
| Neo4j PVC + node replace | Graph is derived but rebuild is slow | Same as today’s EC2 health-only: populate from SoR; do not treat Neo4j as SoR |
| OIDC role too weak on paid | `apply` dies at `eks:CreateCluster` | Widen `github-actions-infra` out of band (same as today’s OIDC bootstrap) |
| Mixing CDK `eks.Cluster` with this Terraform | Duplicate VPC/IAM | CDK stays rejected (estate §6.5) |

---

## 13. Open questions (prove before any apply)

1. **Role name is `LabEksClusterRole` (given).** Still paste `get-role` trust + attached policies before apply (must include `eks.amazonaws.com` **and** `ec2.amazonaws.com`).
2. Can the federated lab user `iam:PassRole` `LabEksClusterRole` to `eks.amazonaws.com` from GitHub Actions keys (same as console)?
3. Does `CreateCluster` succeed with that ARN and **no** node group (control plane only)?
4. Does a managed node group accept the **same** ARN as `node_role_arn` (Vocareum: cluster **and** node)?
5. Credit remaining vs `$0.10`/h × expected cluster lifetime + existing NAT leak. Compose estate **destroyed** first (9-EC2 cap)?
6. Course rubric: cluster-exists (bar A) vs Heavy Rental on Kubernetes (bar B). Bar A does not need Ansible.
7. Paid: may the GitHub OIDC role create IAM roles and an OIDC provider? Paid has no `LabEksClusterRole`.
8. Haystack internal Ingress: how does app CD **verify** `:8000/health` from a GitHub-hosted runner (port-forward vs terraform-owned internal ALB health)?
9. Keep RDS engine pin (prefer **12.22** then **11.22** on this lab) — EKS does not change that.

---

## 14. Summary

The live Heavy Rental cloud pipeline is a **compose-on-EC2 factory**: GitHub Actions → Terraform ASGs/ALBs/RDS → Ansible Docker → app CD `--limit` an ASG. That factory **does not** spin up Amazon EKS.

A **new** GitHub Action, copied from that factory’s *trigger* and *split of work*, **can**:

| Piece | Spin up EKS (cluster + nodes)? |
| --- | --- |
| New `aws-eks-academy.yml` (`workflow_dispatch`, Vocareum keys, `assert-lab`) | **Yes** (orchestrator) |
| New `terraform/eks/` with `role_arn` = `node_role_arn` = **`LabEksClusterRole`**, instance types **nano–large** | **Yes** (creates the cluster) |
| Ansible | **No** for create. **Yes** later for workload config (`kubernetes.core` / `kubectl`), never live `guest_base` |
| Live `aws-infra-academy.yml` + `terraform/academy/` | **No** |

Academy still cannot pause the control plane; do not stack this on the 9-guest compose estate. Full Heavy Rental on the cluster is a later wave. Plan: [`IMPLEMENTATION-PLAN.md`](IMPLEMENTATION-PLAN.md).

Example workflows in this folder are **fail-closed stubs**. Live YAML, if it is ever written, lives in `heavy-rental-project-instructure-and-cloud-deploy`.
