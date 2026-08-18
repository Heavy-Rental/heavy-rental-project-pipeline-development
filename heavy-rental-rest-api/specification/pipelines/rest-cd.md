# REST API Academy CD family

**Application:** https://github.com/Heavy-Rental/heavy-rental-spring-rest-api  
**Authoring tree:** `heavy-rental-rest-api/deploy-pipeline/`  
**Consumes:** public GHCR/ECR tag or Release image tar from the CI family ([`rest-ci.md`](rest-ci.md))

This family discovers `asg-rest` and can re-run REST compose. It does **not** run Terraform or create the ASG. Infra `apply` + `sync-secrets` must already have created the guests and `heavy-rental/rest`. The Release image is env-only (ADR 0007); CD maps SM → `.env` and must not expect JDBC URLs inside the image.

Operator checklist: [`../../docs/PREPARE-SPRING-REPO.md`](../../docs/PREPARE-SPRING-REPO.md). Everyday operate: [`../../docs/BOOTSTRAP.md`](../../docs/BOOTSTRAP.md).

## Actions

```
workflow_dispatch (Environment academy + Vocareum keys)
      │
      ▼
 assert-lab          refuse non-academy; resolve keys (masked); sts
      │
      ▼
 discover-targets    SSM inventory asg-rest
      │
      ├── action=verify           skip compose; SSM GET :8080
      ├── action=configure-only   refresh .env from SM; needs REST_IMAGE or image_ref
      └── action=deploy           resolve-image → ansible rest → verify
```

| Action | Compose? | Image required? |
| --- | --- | --- |
| `verify` | No | No |
| `configure-only` | Yes (refresh `.env`) | `REST_IMAGE` or `image_ref` (or tar **and** matching tag). **No stock Tomcat.** |
| `deploy` | Yes | Same. Prefer a **new** tag. |

`verify` is SSM `GET :8080`. Haystack being down does **not** fail this job by itself.

## Job graph

```
assert-lab
      │
      ▼
 discover-targets
      │
      ├── resolve-image   (deploy / configure-only)
      ├── ansible-rest    guest_base + rest only; --limit rest
      └── verify          SSM GET :8080
```

## Environment `academy`

| Kind | Name | Role |
| --- | --- | --- |
| Secret (optional fallback) | `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_SESSION_TOKEN` | Runner only |
| Variable | `AWS_REGION` | Defaults to `us-east-1` |
| Variable | `REST_IMAGE` | Public GHCR or ECR tag |
| Variable | `IMAGE_HTTP_URL` | Optional HTTPS or `s3://` CI tar |

Do **not** point this workflow at CI Environments `integration` or `production`. Do not copy `REST_API_CLOUD_DB_*` onto the guest.

The **runner** uses Vocareum keys. The **EC2** uses `LabRole`.

## Install into the application repo

| Source | Destination in the Spring repo |
| --- | --- |
| `rest-api-cd-academy-caller.yml` | `.github/workflows/` |
| `rest-api-cd-academy.yml` | `.github/workflows/` |
| `resolve-vocareum-aws/action.yml` | `.github/actions/resolve-vocareum-aws/` |
| `ansible/` | **`deploy-pipeline/ansible/`** (keep this path) |

## Local validation (this repo)

```bash
actionlint heavy-rental-rest-api/deploy-pipeline/rest-api-cd-academy.yml
actionlint heavy-rental-rest-api/deploy-pipeline/rest-api-cd-academy-caller.yml
```

## Pipeline boundaries

| Concern | In this CD family? |
| --- | --- |
| Discover `asg-rest` and compose REST | Yes |
| Terraform / create ASG | No |
| Ansible groups portal / haystack / neo4j | No |
| Rebuild the image | No — consume Release artifacts |
| `stop` / `destroy` | No — infra CD |
| Paid / OIDC | No |

## Specs

- OpenSpec: [`../../openspec/changes/add-rest-cd-academy-skeleton/`](../../openspec/changes/add-rest-cd-academy-skeleton/), [`../../openspec/changes/add-rest-cd-academy-deploy/`](../../openspec/changes/add-rest-cd-academy-deploy/)
- OpenSPDD: [`../../spdd/analysis/add-rest-cd-academy-deploy.md`](../../spdd/analysis/add-rest-cd-academy-deploy.md)
- ADRs 0001–0003: [`../../docs/adr/`](../../docs/adr/)
