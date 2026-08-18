# Web portal Academy CD family

**Application:** Heavy-Rental/heavy-rental-react-web-portal  
**Authoring tree:** `heavy-rental-web-portal-pipeline/deploy-pipeline/`  
**Consumes:** public GHCR/ECR tag or Release image tar from the CI family ([`portal-ci.md`](portal-ci.md))

This family discovers `asg-portal` and can re-run portal compose. It does **not** run Terraform or create the ASG. Infra `apply` + `sync-secrets` must already have created the guests and `heavy-rental/portal` (`REST_BASE_URL` + `pk_`). The Release image is a static SPA (ADR 0007); this CD mounts nginx `/api` → `REST_BASE_URL` over the image `default.conf`.

Operator checklist: [`../../docs/PREPARE-PORTAL-REPO.md`](../../docs/PREPARE-PORTAL-REPO.md). Everyday operate: [`../../docs/BOOTSTRAP.md`](../../docs/BOOTSTRAP.md).

## Actions

```
workflow_dispatch (Environment academy + Vocareum keys)
      │
      ▼
 assert-lab          refuse non-academy; resolve keys (masked); sts
      │
      ▼
 discover-targets    SSM inventory asg-portal
      │
      ├── action=verify           skip compose; SSM GET / on :80
      ├── action=configure-only   refresh .env + /api; stock nginx allowed
      └── action=deploy           resolve-image → ansible portal → verify
```

| Action | Compose? | Image required? |
| --- | --- | --- |
| `verify` | No | No |
| `configure-only` | Yes | `PORTAL_IMAGE` or `image_ref` **or stock `nginx`** |
| `deploy` | Yes | `PORTAL_IMAGE` or `image_ref` (or tar **and** matching tag). Stock nginx **forbidden**. |

`verify` is SSM `GET /` on `:80`. `/api` being down does **not** fail this job by itself.

## Job graph

```
assert-lab
      │
      ▼
 discover-targets
      │
      ├── resolve-image    (deploy / configure-only)
      ├── ansible-portal   guest_base + portal only; --limit portal
      └── verify           SSM GET / on :80
```

## Environment `academy`

| Kind | Name | Role |
| --- | --- | --- |
| Secret (optional fallback) | `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_SESSION_TOKEN` | Runner only |
| Variable | `AWS_REGION` | Defaults to `us-east-1` |
| Variable | `PORTAL_IMAGE` | Public GHCR or ECR tag |
| Variable | `IMAGE_HTTP_URL` | Optional HTTPS or `s3://` CI tar |

Do **not** point this workflow at CI Environments `integration` or `production`.

The **runner** uses Vocareum keys. The **EC2** uses `LabRole`.

## Install into the application repo

| Source | Destination in the React repo |
| --- | --- |
| `portal-cd-academy-caller.yml` | `.github/workflows/` |
| `web-portal-cd-academy.yml` | `.github/workflows/` |
| `resolve-vocareum-aws/action.yml` | `.github/actions/resolve-vocareum-aws/` |
| `ansible/` | **`deploy-pipeline/ansible/`** (keep this path) |

## Local validation (this repo)

```bash
actionlint heavy-rental-web-portal-pipeline/deploy-pipeline/web-portal-cd-academy.yml
actionlint heavy-rental-web-portal-pipeline/deploy-pipeline/portal-cd-academy-caller.yml
```

## Pipeline boundaries

| Concern | In this CD family? |
| --- | --- |
| Discover `asg-portal` and compose portal | Yes |
| Terraform / create ASG | No |
| Ansible groups rest / haystack / neo4j | No |
| Rebuild the image | No — consume Release artifacts |
| `stop` / `destroy` | No — infra CD |

## Specs

- OpenSpec: [`../../openspec/changes/add-portal-cd-academy-skeleton/`](../../openspec/changes/add-portal-cd-academy-skeleton/), [`../../openspec/changes/add-portal-cd-academy-deploy/`](../../openspec/changes/add-portal-cd-academy-deploy/)
- OpenSPDD: [`../../spdd/analysis/add-portal-cd-academy-deploy.md`](../../spdd/analysis/add-portal-cd-academy-deploy.md)
- ADRs 0001–0003: [`../../docs/adr/`](../../docs/adr/)
