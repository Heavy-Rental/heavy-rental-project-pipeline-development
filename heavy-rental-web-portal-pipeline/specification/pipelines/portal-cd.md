# Web portal app CD family (Academy + paid)

**Application:** Heavy-Rental/heavy-rental-react-web-portal  
**Authoring tree:** `heavy-rental-web-portal-pipeline/deploy-pipeline/`  
**Consumes:** public GHCR/ECR tag or Release image tar from the CI family ([`portal-ci.md`](portal-ci.md))

This family discovers `asg-portal` and can re-run portal compose. It does **not** run Terraform or create the ASG. Infra `aws-infra-academy.yml` `apply` + `sync-secrets` must already have created the guests and `heavy-rental/portal` (`REST_BASE_URL=http://<rest_alb>:8080` + Stripe `pk_`). The Release image is a React/Vite static SPA (ADR 0007 / 0008); this CD mounts nginx `/api` → `REST_BASE_URL` over the image `default.conf`. GitHub `VITE_*` does not overlay the bundle. Spring REST owns Haystack, CORS, JWT, RDS, and Stripe `sk_`.

Operator checklist: [`../../docs/PREPARE-PORTAL-REPO.md`](../../docs/PREPARE-PORTAL-REPO.md). Everyday operate: [`../../docs/BOOTSTRAP.md`](../../docs/BOOTSTRAP.md).

## Actions

```
Two callers (same reusable jobs):
  portal-cd-academy-caller.yml     Environment academy + Vocareum keys
  portal-cd-paid-caller.yml        Environment AWS_ACTUAL + OIDC, no Vocareum keys
      │
      ▼
 assert               academy: refuse non-academy, resolve keys (masked), sts
                      paid: refuse non-AWS_ACTUAL, OIDC, no AWS_ACCESS_KEY_ID
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
| `configure-only` | Yes (refresh guest `.env` + `/api`; does **not** run `npm` or rebuild the image) | `PORTAL_IMAGE` or `image_ref` **or stock `nginx`** |
| `deploy` | Yes | `PORTAL_IMAGE` or `image_ref` (or tar **and** matching tag). Stock nginx **forbidden**. |

`verify` is SSM `GET /` on `:80`. `/api` being down does **not** fail this job by itself.

## Job graph

```
assert (academy Vocareum | paid OIDC)
      │
      ▼
 discover-targets
      │
      ├── resolve-image    (deploy only; stock nginx forbidden)
      ├── ansible-portal   guest_base + portal only; --limit portal
      └── verify           SSM GET / on :80
```

Paid Ansible SSM uses `heavy-rental-ssm-<account>-actual` (not the tfstate bucket). Academy keeps the tfstate bucket for SSM transfer. `REST_BASE_URL` is the **internet-facing** REST ALB (`http://<rest_alb_dns>:8080`, infra ADR 0018).

## Environment `academy`

| Kind | Name | Role |
| --- | --- | --- |
| Secret (optional fallback) | `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_SESSION_TOKEN` | Runner only (or Run form). Never on the EC2 |
| Variable | `AWS_REGION` | Defaults to `us-east-1` |
| Variable | `PORTAL_IMAGE` | Public GHCR or ECR tag. Empty on `configure-only` → stock `nginx` |
| Variable | `IMAGE_HTTP_URL` | Optional HTTPS or `s3://` CI tar |
| Variable | `VITE_STRIPE_PUBLISHABLE_KEY` | Optional `pk_`. Overlay guest `.env` on deploy/configure-only. Browser still uses the key baked at Release |

Do **not** set `REST_BASE_URL`, other `VITE_*`, `VITE_API_TARGET`, Stripe `sk_` / `whsec_`, `HAYSTACK_BASE_URL`, CORS, JWT, or RDS here. `VITE_STRIPE_PUBLISHABLE_KEY` (`pk_` only) is the exception.

Do **not** point this workflow at CI Environments `integration` or `production`.

The academy **runner** uses Vocareum keys. The academy **EC2** uses `LabRole`.

## Environment `AWS_ACTUAL`

| Kind | Name | Role |
| --- | --- | --- |
| Variable or secret | `AWS_ROLE_TO_ASSUME` | GitHub OIDC. Required on paid |
| Variable | `AWS_REGION` | Defaults to `us-east-1` |
| Variable | `PORTAL_IMAGE` | Public GHCR or ECR tag. Empty on `configure-only` → stock `nginx` |
| Variable | `IMAGE_HTTP_URL` | Optional HTTPS or `s3://` CI tar |
| Variable | `VITE_STRIPE_PUBLISHABLE_KEY` | Optional `pk_`. Overlay guest `.env`. Browser still uses the key baked at Release |

Paid caller declares **no** Vocareum key inputs. It fails if Environment is not `AWS_ACTUAL`, if `AWS_ACCESS_KEY_ID` is set, or if `AWS_ROLE_TO_ASSUME` is empty. The **EC2** uses `hr-paid-portal`. Do **not** set `REST_BASE_URL`, other `VITE_*`, Stripe `sk_` / `whsec_`, or RDS here. `VITE_STRIPE_PUBLISHABLE_KEY` (`pk_` only) is the exception.

## configure-only configuration (three stores)

`configure-only` does **not** read the React repo `.env.api` / `.env.mock` / `.env.production` and does **not** run `npm`.

| Store | Used? | Keys |
| --- | --- | --- |
| GitHub Environment `academy` | Runner + compose tag + Stripe `pk_` | Vocareum secrets or form; `AWS_REGION`; `PORTAL_IMAGE` (or stock `nginx`); `IMAGE_HTTP_URL`; `VITE_STRIPE_PUBLISHABLE_KEY` |
| Guest `/opt/heavy-rental/.env` | Yes — SM then academy overlay | **Required** `REST_BASE_URL`. Academy `pk_` overlays SM when set. Browser checkout still uses the key **baked at Release** |
| App Vite dotenv | **No** | Release `vite build` only (`MODE=api` is a build flag) |

Infra `aws-infra-academy.yml` `sync-secrets` must have filled `heavy-rental/portal` first. Changing the REST host is infra then this `configure-only`. Changing SPA login/`MODE` or Stripe `pk_` in JS is a new Release image (`vite build --mode api`) + `action=deploy`. Guest `/api` then reaches Spring REST on the ALB.

## Install into the application repo

| Source | Destination in the React repo |
| --- | --- |
| `portal-cd-academy-caller.yml` | `.github/workflows/` |
| `portal-cd-paid-caller.yml` | `.github/workflows/` |
| `web-portal-cd-academy.yml` | `.github/workflows/` |
| `resolve-vocareum-aws/action.yml` | `.github/actions/resolve-vocareum-aws/` |
| `resolve-aws-profile/action.yml` | `.github/actions/resolve-aws-profile/` |
| `ansible/` | **`deploy-pipeline/ansible/`** (keep this path) |

## Local validation (this repo)

```bash
actionlint heavy-rental-web-portal-pipeline/deploy-pipeline/web-portal-cd-academy.yml
actionlint heavy-rental-web-portal-pipeline/deploy-pipeline/portal-cd-academy-caller.yml
actionlint heavy-rental-web-portal-pipeline/deploy-pipeline/portal-cd-paid-caller.yml
```

## Pipeline boundaries

| Concern | In this CD family? |
| --- | --- |
| Discover `asg-portal` and compose portal | Yes |
| Terraform / create ASG | No |
| Ansible groups rest / haystack / neo4j | No |
| Rebuild the image | No — consume Release artifacts |
| `stop` / `destroy` | No — infra CD |
| Paid / OIDC | Yes — `portal-cd-paid-caller.yml` (ADR 0009) |

## Specs

- OpenSpec: [`../../openspec/changes/add-portal-cd-academy-skeleton/`](../../openspec/changes/add-portal-cd-academy-skeleton/), [`../../openspec/changes/add-portal-cd-academy-deploy/`](../../openspec/changes/add-portal-cd-academy-deploy/), [`../../openspec/changes/add-portal-cd-paid-deploy/`](../../openspec/changes/add-portal-cd-paid-deploy/)
- OpenSPDD: [`../../spdd/analysis/add-portal-cd-academy-deploy.md`](../../spdd/analysis/add-portal-cd-academy-deploy.md), [`../../spdd/analysis/add-portal-cd-paid-deploy.md`](../../spdd/analysis/add-portal-cd-paid-deploy.md)
- ADRs 0001–0003, 0007–0009: [`../../docs/adr/`](../../docs/adr/)
