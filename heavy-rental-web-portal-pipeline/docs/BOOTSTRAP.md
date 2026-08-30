# Portal app CD (Academy + paid)

This workflow discovers `asg-portal` and can re-run portal compose (branch 2). It does **not** run Terraform or create the ASG. The Release image is a **React + Vite static SPA** (`vite build --mode api` → nginx). This CD mounts nginx `/api` → `REST_BASE_URL`.

Specification index: [`../specification/README.md`](../specification/README.md). CD walkthrough: [`../specification/pipelines/portal-cd.md`](../specification/pipelines/portal-cd.md). App-repo checklist: [`PREPARE-PORTAL-REPO.md`](PREPARE-PORTAL-REPO.md). GHCR publish (dispatch Release after merge; Publish creates the GitHub Release; no `GITHUB_TOKEN` secret): [`GHCR-RELEASE.md`](GHCR-RELEASE.md). Vite scan sample: [`samples/.env.production`](samples/.env.production) (Release scans it; `--mode api` loads `.env.api`).

Install from **`deploy-pipeline/`** into the React repo (same paths as PREPARE §4):

- `portal-cd-academy-caller.yml` → `.github/workflows/`
- `portal-cd-paid-caller.yml` → `.github/workflows/` (billed AWS)
- `web-portal-cd-academy.yml` → `.github/workflows/` (shared jobs)
- `resolve-aws-profile/action.yml` → `.github/actions/resolve-aws-profile/`
- **`ansible/`** → `deploy-pipeline/ansible/` (keep this path)

Do **not** copy `resolve-vocareum-aws/` (portal CD does not `uses:` it; `resolve-aws-profile` already masks Vocareum keys).

Do **not** copy `specification/`. Copy [`samples/.env.production`](samples/.env.production) to the **React** repo as `.env.production` (Release **scan** input). GHCR is built with **`vite build --mode api`** (loads `.env.api`, not `.env.production`) so Spring login works. Vite inlines `VITE_*` at build time; CD does not read the file.

## Env ownership (Spring REST + AWS)

Infra `aws-infra-academy.yml` `configure-only` / `apply` runs `scripts/sync-secrets.sh` after Terraform. ALB DNS comes from Terraform outputs. Stripe / JWT / OneMap come from infra Environment `academy` secrets.

| Owner | Keys | Who reads them |
| --- | --- | --- |
| Terraform → `heavy-rental/portal` | `REST_BASE_URL=http://<rest_alb_dns>:8080` | Portal CD nginx `/api` (not the JS bundle) |
| Infra academy Stripe `pk_` → portal SM | `STRIPE_PUBLISHABLE_KEY`, `VITE_STRIPE_PUBLISHABLE_KEY` | Stored on the guest `.env`. The static SPA **cannot** read SM. Bake `pk_` only via academy `VITE_STRIPE_PUBLISHABLE_KEY` + new `vite build --mode api` |
| Terraform → `heavy-rental/rest` | `HAYSTACK_BASE_URL=http://<haystack_alb_dns>:8000`, `APP_CORS_ALLOWED_ORIGINS=http://<portal_alb_dns>,http://<rest_alb_dns>:8080` (ADR 0018), SoR `POSTGRES_*` | **Spring REST** (`application-prod.properties` `${…}`). Not the React SPA |
| Infra academy secrets → REST SM | `STRIPE_API_KEY`, `STRIPE_WEBHOOK_SECRET`, `APP_JWT_SECRET`, optional OneMap, optional pricing vars | **Spring REST** only. Never in Vite or the nginx image |
| Image `dist/` from `vite build --mode api` | `MODE=api` + empty `VITE_API_TARGET` / `VITE_*` backends (same-origin `/api`) | Browser JS → guest `/api` → NAT → public REST ALB → Spring REST |
| Portal Environment `academy` (or `AWS_ACTUAL`) | `PORTAL_IMAGE`, `IMAGE_HTTP_URL`, Vocareum keys (academy) or OIDC role (paid), optional `VITE_STRIPE_PUBLISHABLE_KEY` (`pk_`) | Which tag to pull. Packaging (academy only) bakes `pk_`. CD overlays `pk_` onto guest `.env` only — **not** the SPA bundle. Other `VITE_*` stay off these Environments |

Setting a GitHub `VITE_*` variable does **not** rebuild GHCR and does **not** reconfigure the running SPA. CD may overlay `VITE_STRIPE_PUBLISHABLE_KEY` (`pk_` only) onto guest `.env`; nginx does not run Node, so the browser still uses the key **baked at Release**. That is not a Haystack-style process-env overlay.

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

Create Environment **`AWS_ACTUAL`**. Variable `AWS_ROLE_TO_ASSUME` (OIDC). Same `AWS_REGION` / `PORTAL_IMAGE` / `IMAGE_HTTP_URL` / `VITE_STRIPE_PUBLISHABLE_KEY` on **this** Environment. **No** `AWS_ACCESS_KEY_ID`. Do **not** pass `secrets: inherit` (OIDC uses `vars.AWS_ROLE_TO_ASSUME` + `id-token`). Trust the role for this app repo. Run **Web Portal CD (paid)** after infra **AWS infrastructure (paid)** `apply`. Ansible SSM uses `heavy-rental-ssm-<account>-actual`.

## configure-only (same as [`../specification/pipelines/portal-cd.md`](../specification/pipelines/portal-cd.md))

Does **not** read `.env.api` / `.env.production` and does **not** run `npm`.

| Store | Used? | Keys |
| --- | --- | --- |
| GitHub `academy` or `AWS_ACTUAL` | Runner + compose tag + Stripe `pk_` | Vocareum keys or form (academy only); OIDC role (`AWS_ACTUAL`); `AWS_REGION`; `PORTAL_IMAGE` (empty → stock `nginx`); `IMAGE_HTTP_URL`; `VITE_STRIPE_PUBLISHABLE_KEY` |
| Guest `/opt/heavy-rental/.env` | Yes — SM then academy overlay | **Required** `REST_BASE_URL`. SM `pk_` unless academy `VITE_STRIPE_PUBLISHABLE_KEY` overlays it. SPA still uses the **baked** Release key. Refuse `sk_` / webhook / PEM |
| App Vite dotenv | **No** | Release only |

Infra must already have applied the estate and `sync-secrets` (`heavy-rental/portal`). Infra `apply` does **not** compose portal; first compose is infra `deploy-projects` or this CD `action=deploy`. Guests InService + SSM Online.

## Every run (same as PREPARE §7)

1. Instructure → Start Lab → AWS Details.
2. Actions → **Web Portal CD (Academy)** → Environment `academy` → paste Vocareum keys (or Environment fallback).
3. `action=verify` — assert-lab + discover + SSM `GET /` on `:80` (`/api` down does not fail this job by itself).
4. `action=deploy` — **new** public GHCR or ECR tag (or tar + matching tag). Stock nginx **forbidden**. Prefer a **new tag**.
5. `action=configure-only` — refresh guest `.env` + nginx `/api` from `heavy-rental/portal`. Stock nginx allowed.

The **runner** uses Vocareum keys. The **EC2** uses `LabRole`.

## Do not (same as PREPARE §8)

- Use CI Environments `integration` / `production` as CD
- Put Stripe `sk_` / `whsec_` or Vocareum keys in the image or `.env.production`. Vocareum keys **belong** on the academy Run form (or Environment fallback); never in SM or on the EC2
- Bake `REST_BASE_URL` / Haystack ALB / `localhost:8080` into `vite build --mode api`
- Expect GitHub `VITE_*` vars to reconfigure the running SPA
- Type instance IDs on the Run form
- Run `terraform apply` from this workflow
- Expect GHCR from a `develop` → `master` PR alone (run **Actions → Release** after merge; the pipeline creates the GitHub Release)
- Treat a green `verify` as proof that `/api` reached REST

Release `workflow_dispatch` **Packaging** uploads `heavy_rental_web_portal-image.tar.gz`. **Publish** pushes `ghcr.io/<owner>/heavy_rental_web_portal:<x.y.z>` and `:latest` and creates the GitHub Release (zip + DAST assets, not the tar).
