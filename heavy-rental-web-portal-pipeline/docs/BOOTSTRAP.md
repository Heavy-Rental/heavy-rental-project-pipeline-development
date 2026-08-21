# Portal app CD (Academy)

This workflow discovers `asg-portal` and can re-run portal compose (branch 2). It does **not** run Terraform or create the ASG. The Release image is a **React + Vite static SPA** (`npm run build` → nginx). This CD mounts nginx `/api` → `REST_BASE_URL`.

Specification index: [`../specification/README.md`](../specification/README.md). CD walkthrough: [`../specification/pipelines/portal-cd.md`](../specification/pipelines/portal-cd.md). App-repo checklist: [`PREPARE-PORTAL-REPO.md`](PREPARE-PORTAL-REPO.md). GHCR publish (login skipped on PR, no `GITHUB_TOKEN` secret): [`GHCR-RELEASE.md`](GHCR-RELEASE.md). Vite production sample: [`samples/.env.production`](samples/.env.production).

Install from **`deploy-pipeline/`** into the React repo (same paths as PREPARE §4):

- `portal-cd-academy-caller.yml` → `.github/workflows/`
- `portal-cd-paid-caller.yml` → `.github/workflows/` (billed AWS)
- `web-portal-cd-academy.yml` → `.github/workflows/` (shared jobs)
- `resolve-vocareum-aws/action.yml` → `.github/actions/resolve-vocareum-aws/`
- `resolve-aws-profile/action.yml` → `.github/actions/resolve-aws-profile/`
- **`ansible/`** → `deploy-pipeline/ansible/` (keep this path)

Do **not** copy `specification/`. Copy [`samples/.env.production`](samples/.env.production) to the **React** repo as `.env.production` (scanned at Release). GHCR is built with **`vite build --mode api`** so Spring login works. Vite inlines `VITE_*` at build time; CD does not read the file.

## Env ownership (Spring REST + AWS)

Infra `aws-infra-academy.yml` `configure-only` / `apply` runs `scripts/sync-secrets.sh` after Terraform. ALB DNS comes from Terraform outputs. Stripe / JWT / OneMap come from infra Environment `academy` secrets.

| Owner | Keys | Who reads them |
| --- | --- | --- |
| Terraform → `heavy-rental/portal` | `REST_BASE_URL=http://<rest_alb_dns>:8080` | Portal CD nginx `/api` (not the JS bundle) |
| Infra academy Stripe `pk_` → portal SM | `STRIPE_PUBLISHABLE_KEY`, `VITE_STRIPE_PUBLISHABLE_KEY` | Stored on the guest `.env`. The static SPA **cannot** read SM. Bake `pk_` only via app `.env.production` + new `npm run build` |
| Terraform → `heavy-rental/rest` | `HAYSTACK_BASE_URL=http://<haystack_alb_dns>:8000`, `APP_CORS_ALLOWED_ORIGINS=http://<portal_alb_dns>`, SoR `POSTGRES_*` | **Spring REST** (`application-prod.properties` `${…}`). Not the React SPA |
| Infra academy secrets → REST SM | `STRIPE_API_KEY`, `STRIPE_WEBHOOK_SECRET`, `APP_JWT_SECRET`, optional OneMap, optional pricing vars | **Spring REST** only. Never in Vite or the nginx image |
| Image `dist/` from `vite build --mode api` | `MODE=api` + empty `VITE_API_TARGET` / `VITE_*` backends (same-origin `/api`) | Browser JS → guest `/api` → Spring REST |
| Portal Environment `academy` | `PORTAL_IMAGE`, `IMAGE_HTTP_URL`, Vocareum keys | Which tag to pull. **Not** SPA `VITE_*` |

Setting a GitHub `VITE_*` variable on portal Environment `academy` does **not** change GHCR or the running React app. There is no haystack-style overlay for Vite.

Haystack is private (REST → Haystack). The SPA must not call Haystack or RDS.

## GitHub Environment `academy`

Do **not** point CD at CI Environments `integration` or `production`.

### Secrets (runner only — optional fallback)

| Secret | When required |
| --- | --- |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_SESSION_TOKEN` | If the Run form fields are empty. Never on the EC2 or in SM. |

### Variables

| Variable | Required? | Role |
| --- | --- | --- |
| `AWS_REGION` | Recommended | Defaults to `us-east-1` |
| `PORTAL_IMAGE` | Required for `deploy` unless `image_ref` is set | Public GHCR or ECR tag. Empty allowed for `configure-only` (stock `nginx`). **Not** a Vite knob |
| `IMAGE_HTTP_URL` | Optional | HTTPS or `s3://` CI tar |
| `VITE_STRIPE_PUBLISHABLE_KEY` | Optional (`pk_` only) | Release Packaging (`environment: academy`) bakes it into the JS bundle. CD overlays guest `.env`. Empty leaves `.env.api` / SM. **Never** `sk_` |

Do **not** set `REST_BASE_URL`, `HAYSTACK_BASE_URL`, other `VITE_*`, `VITE_API_TARGET`, Stripe `sk_` / `whsec_`, or `APP_CORS_*` here. Infra SM + CD `/api` own the REST host. Changing Stripe `pk_` in the **browser** still needs a new Release image; CD overlay does not rewrite `dist/`.

## GitHub Environment `AWS_ACTUAL` (paid)

Create Environment **`AWS_ACTUAL`**. Variable `AWS_ROLE_TO_ASSUME` (OIDC). Same `AWS_REGION` / `PORTAL_IMAGE` / `IMAGE_HTTP_URL` / `VITE_STRIPE_PUBLISHABLE_KEY` on **this** Environment. **No** `AWS_ACCESS_KEY_ID`. Trust the role for this app repo. Run **Web Portal CD (paid)** after infra **AWS infrastructure (paid)** `apply`. Ansible SSM uses `heavy-rental-ssm-<account>-actual`.

## configure-only (same as [`../specification/pipelines/portal-cd.md`](../specification/pipelines/portal-cd.md))

Does **not** read `.env.api` / `.env.production` and does **not** run `npm`.

| Store | Used? | Keys |
| --- | --- | --- |
| GitHub `academy` | Runner + compose tag + Stripe `pk_` | Vocareum keys or form; `AWS_REGION`; `PORTAL_IMAGE` (empty → stock `nginx`); `IMAGE_HTTP_URL`; `VITE_STRIPE_PUBLISHABLE_KEY` |
| Guest `/opt/heavy-rental/.env` | Yes — SM then academy overlay | **Required** `REST_BASE_URL`. SM `pk_` unless academy `VITE_STRIPE_PUBLISHABLE_KEY` overlays it. SPA still uses the **baked** Release key. Refuse `sk_` / webhook / PEM |
| App Vite dotenv | **No** | Release only |

Infra must already have applied the estate and `sync-secrets` (`heavy-rental/portal`). Guests InService + SSM Online.

## Every run (same as PREPARE §7)

1. Instructure → Start Lab → AWS Details.
2. Actions → **Web Portal CD (Academy)** → Environment `academy` → paste Vocareum keys (or Environment fallback).
3. `action=verify` — assert-lab + discover + SSM `GET /` on `:80` (`/api` down does not fail this job by itself).
4. `action=deploy` — **new** public GHCR or ECR tag (or tar + matching tag). Stock nginx **forbidden**. Prefer a **new tag**.
5. `action=configure-only` — refresh guest `.env` + nginx `/api` from `heavy-rental/portal`. Stock nginx allowed.

The **runner** uses Vocareum keys. The **EC2** uses `LabRole`.

## Do not (same as PREPARE §8)

- Use CI Environments `integration` / `production` as CD
- Put Vocareum keys or Stripe `sk_` in the image, in `.env.production`, or on the Run form
- Bake `REST_BASE_URL` / Haystack ALB / `localhost:8080` into `npm run build`
- Expect GitHub `VITE_*` vars to reconfigure the running SPA
- Type instance IDs on the Run form
- Run `terraform apply` from this workflow
- Expect GHCR from a `develop` → `master` PR alone (run **Actions → Release** after merge; the pipeline creates the GitHub Release)
- Treat a green `verify` as proof that `/api` reached REST
