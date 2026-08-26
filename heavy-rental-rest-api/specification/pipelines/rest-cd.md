# REST API app CD family (Academy + paid)

**Application:** https://github.com/Heavy-Rental/heavy-rental-spring-rest-api  
**Authoring tree:** `heavy-rental-rest-api/deploy-pipeline/`  
**Consumes:** public GHCR/ECR tag or Release image tar from the CI family ([`rest-ci.md`](rest-ci.md))

This family discovers `asg-rest` and can re-run REST compose. It does **not** run Terraform or create the ASG. Infra `apply` + `sync-secrets` must already have created the guests and `heavy-rental/rest`. The Release image is env-only (ADR 0007); CD maps SM → `.env` and must not expect JDBC URLs inside the image.

Operator checklist: [`../../docs/PREPARE-SPRING-REPO.md`](../../docs/PREPARE-SPRING-REPO.md). Everyday operate: [`../../docs/BOOTSTRAP.md`](../../docs/BOOTSTRAP.md).

## Actions

```
Two callers (same reusable jobs):
  rest-api-cd-academy-caller.yml   Environment academy + Vocareum keys
  rest-api-cd-paid-caller.yml      Environment AWS_ACTUAL + OIDC, no Vocareum keys
      │
      ▼
 Assert Environment academy | Assert Environment AWS_ACTUAL
      │
      ▼
 Assert AWS profile          academy: Vocareum keys (masked) + sts
                             paid: OIDC, no AWS_ACCESS_KEY_ID
      │
      ▼
 Discover asg-rest
      │
      ├── action=verify           skip compose; Health GET :8080
      ├── action=configure-only   ansible-rest (no resolve-image); needs REST_IMAGE or image_ref
      └── action=deploy           Resolve CI image → ansible-rest → Health GET :8080
```

| Action | Compose? | Image required? |
| --- | --- | --- |
| `verify` | No | No |
| `configure-only` | Yes (refresh `.env`) | `REST_IMAGE` or `image_ref` (or tar **and** matching tag). **No stock Tomcat.** |
| `deploy` | Yes | Same. Prefer a **new** tag. |

`verify` is SSM `GET :8080`. Haystack being down does **not** fail this job by itself.

## Job graph

```
Assert Environment academy | Assert Environment AWS_ACTUAL
      │
      ▼
 Assert AWS profile
      │
      ▼
 Discover asg-rest
      │
      ├── Resolve CI image     (deploy only)
      ├── Compose playbook     guest_base + rest; --limit rest
      │                        (deploy and configure-only)
      └── Health GET :8080
```

Job `name:` values: `Assert Environment academy` / `Assert Environment AWS_ACTUAL` (callers), then `Assert AWS profile`, `Discover asg-rest`, `Resolve CI image`, `Compose playbook on asg-rest`, `Health GET :8080`. Paid caller uses `secrets: inherit` (OIDC / Environment); academy caller does not. That inherit rule is CI-only.

Paid Ansible SSM uses `heavy-rental-ssm-<account>-actual` (not the tfstate bucket). Academy keeps the tfstate bucket for SSM transfer. REST ALB is internet-facing :8080 (infra ADR 0018); guests stay private.

## Environment `academy`

| Kind | Name | Role |
| --- | --- | --- |
| Secret (optional fallback) | `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_SESSION_TOKEN` | Runner only |
| Variable | `AWS_REGION` | Defaults to `us-east-1` |
| Variable | `REST_IMAGE` | Public GHCR or ECR tag |
| Variable | `IMAGE_HTTP_URL` | Optional HTTPS or `s3://` CI tar |

Do **not** point this workflow at CI Environments `integration` or `production`. Do not copy `REST_API_DB_*` onto the guest.

The academy **runner** uses Vocareum keys. The academy **EC2** uses `LabRole`.

## Environment `AWS_ACTUAL`

| Kind | Name | Role |
| --- | --- | --- |
| Variable or secret | `AWS_ROLE_TO_ASSUME` | GitHub OIDC. Required on paid |
| Variable | `AWS_REGION` | Defaults to `us-east-1` |
| Variable | `REST_IMAGE` | Public GHCR or ECR tag (**this** Environment’s copy) |
| Variable | `IMAGE_HTTP_URL` | Optional HTTPS or `s3://` CI tar |

Paid caller declares **no** Vocareum key inputs. It fails if Environment is not `AWS_ACTUAL`, if `AWS_ACCESS_KEY_ID` is set, or if `AWS_ROLE_TO_ASSUME` is empty. The **EC2** uses `hr-paid-rest`. Do **not** copy `REST_API_DB_*` onto the guest.

## Install into the application repo

| Source | Destination in the Spring repo |
| --- | --- |
| `rest-api-cd-academy-caller.yml` | `.github/workflows/` |
| `rest-api-cd-paid-caller.yml` | `.github/workflows/` |
| `rest-api-cd-academy.yml` | `.github/workflows/` |
| `resolve-vocareum-aws/action.yml` | `.github/actions/resolve-vocareum-aws/` |
| `resolve-aws-profile/action.yml` | `.github/actions/resolve-aws-profile/` |
| `ansible/` | **`deploy-pipeline/ansible/`** (keep this path) |

## Local validation (this repo)

```bash
actionlint heavy-rental-rest-api/deploy-pipeline/rest-api-cd-academy.yml
actionlint heavy-rental-rest-api/deploy-pipeline/rest-api-cd-academy-caller.yml
actionlint heavy-rental-rest-api/deploy-pipeline/rest-api-cd-paid-caller.yml
```

## Pipeline boundaries

| Concern | In this CD family? |
| --- | --- |
| Discover `asg-rest` and compose REST | Yes |
| Terraform / create ASG | No |
| Ansible groups portal / haystack / neo4j | No |
| Rebuild the image | No — consume Release artifacts |
| `stop` / `destroy` | No — infra CD |
| Paid / OIDC | Yes — `rest-api-cd-paid-caller.yml` (ADR 0008) |

## Specs

- OpenSpec: [`../../openspec/changes/add-rest-cd-academy-skeleton/`](../../openspec/changes/add-rest-cd-academy-skeleton/), [`../../openspec/changes/add-rest-cd-academy-deploy/`](../../openspec/changes/add-rest-cd-academy-deploy/), [`../../openspec/changes/add-rest-cd-paid-deploy/`](../../openspec/changes/add-rest-cd-paid-deploy/)
- OpenSPDD: [`../../spdd/analysis/add-rest-cd-academy-deploy.md`](../../spdd/analysis/add-rest-cd-academy-deploy.md), [`../../spdd/analysis/add-rest-cd-paid-deploy.md`](../../spdd/analysis/add-rest-cd-paid-deploy.md)
- ADRs 0001–0003, 0008: [`../../docs/adr/`](../../docs/adr/)
