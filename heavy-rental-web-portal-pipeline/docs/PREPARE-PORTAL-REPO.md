# Prepare the React portal for Academy CD

**App repo:** [Heavy-Rental/heavy-rental-react-web-portal](https://github.com/Heavy-Rental/heavy-rental-react-web-portal)  
**Release CI:** `release-pipeline/` in this tree (copy into the app repo `.github/workflows/`)  
**App CD:** `deploy-pipeline/` (this tree — copy when ready)  
**Estate:** infra `apply` + `sync-secrets` must have created `asg-portal` and `heavy-rental/portal`

This file is the operator checklist. It does not apply Terraform or push images.

Everyday operate after install (academy inventory, every-run steps, do-nots): [`BOOTSTRAP.md`](BOOTSTRAP.md). Specification: [`../specification/pipelines/portal-cd.md`](../specification/pipelines/portal-cd.md). Vite production sample: [`samples/.env.production`](samples/.env.production).

This is a **React + npm + Vite** SPA. Spring REST ([heavy-rental-spring-rest-api](https://github.com/Heavy-Rental/heavy-rental-spring-rest-api)) owns `/api`. Infra `aws-infra-academy.yml` writes ALB DNS and Stripe into Secrets Manager. Do not copy REST `application-prod.properties` keys into Vite.

---

## 1. Can Release build the image CD expects?

**Yes, when Release runs in the app repo.** The SPA matches the packaging contract.

| App | Release / CD contract |
| --- | --- |
| Node **22**, `package-lock.json`, Vite `npm run build` | `dist/index.html` + hashed JS/CSS |
| Static SPA | `nginx:1.27-alpine` serving `dist/` (try_files only). CD **replaces** `default.conf` with `/api` → `REST_BASE_URL` |
| App `Dockerfile` ignored | Release **always** generates the nginx + Vite `dist/` image. A Node/Vite-preview Dockerfile is not used for GHCR/CD |
| Same-origin `/api` + Spring login | Release `tsc -b` + **`vite build --mode api`**. Process env empties `VITE_API_TARGET` (do not bake `http://heavy-rental-rest-api:8080`). CD mounts `/api` → SM `REST_BASE_URL` |

Packaging seeds/scans `.env.production`, then `tsc -b` + `vite build --mode api` (empty `VITE_API_TARGET`). It scans `dist/` and the image for `sk_`, lab hosts, and `heavy-rental-rest-api`. Stripe `pk_` is allowed. Generated nginx has no `proxy_pass` host and does **not** `COPY` `.env`. After `action=deploy`, the browser uses same-origin `/api` against Spring REST.

Operator checklist: [`samples/.env.production`](samples/.env.production). Copy it to the React repo root as `.env.production`.

GHCR name: `ghcr.io/<owner>/heavy_rental_web_portal` (lowercase). On `Heavy-Rental` that is `ghcr.io/heavy-rental/heavy_rental_web_portal:<x.y.z>` and `:latest`. The version tag is the previous GHCR semver with the patch bumped (first publish is `1.0.0`).

| Release trigger | What you get |
| --- | --- |
| PR `develop` → `master` | `dist/` zip + docker **tar artifact**. **No GHCR push.** Login is skipped. |
| **Published GitHub Release** | Tar **and** GHCR `<version>` + `:latest` |

Step-by-step (do not set `GITHUB_TOKEN`, why login is skipped, publish Release, public package, `PORTAL_IMAGE`): [`GHCR-RELEASE.md`](GHCR-RELEASE.md).

Academy guests pull **public** GHCR with no token. A PR build is not enough for `PORTAL_IMAGE=ghcr.io/…` unless you `docker load` the tar (`image_http_url` / `IMAGE_HTTP_URL`) or copy the image to ECR.

`DEFAULT_APP_REPOSITORY: SA62-team1/heavy-rental-react-web-portal` in the reusable YAML is only for local `act`. When Release runs **in** the Heavy-Rental portal repo, checkout is the calling repo (into `app/`).

---

## 2. Already on the app repo vs still to copy

Typical app `develop` today:

- Present or pending: Fast Feedback, Integration, Release (copy from this tree)
- **Missing until you copy:** `deploy-pipeline/` (CD caller, reusable workflow, `resolve-vocareum-aws`, `ansible/`)

Do **not** copy `specification/`.

---

## 3. Produce a pullable image

1. Merge to `master` and **publish a GitHub Release**. That is what pushes GHCR.
2. Org Packages → `heavy_rental_web_portal` → visibility **Public**. Private GHCR fails CD on purpose (no PAT on the guest).
3. Record the tag, for example `ghcr.io/heavy-rental/heavy_rental_web_portal:1.0.0` (or `:latest`). Prefer a **new** version tag each deploy (`compose up` is not `--pull always`).

Optional Academy path: upload the Release tar to lab S3 and set `IMAGE_HTTP_URL` / `image_http_url`. The tar includes the GHCR tags, so `PORTAL_IMAGE=ghcr.io/<owner>/heavy_rental_web_portal:<x.y.z>` (or `:latest`) matches after `docker load`.

---

## 4. Install portal app CD into the React repo

Copy from this tree’s `deploy-pipeline/`:

| Source | Destination in the React repo |
| --- | --- |
| `portal-cd-academy-caller.yml` | `.github/workflows/` |
| `portal-cd-paid-caller.yml` | `.github/workflows/` (billed AWS / OIDC) |
| `web-portal-cd-academy.yml` | `.github/workflows/` (shared jobs) |
| `resolve-vocareum-aws/action.yml` | `.github/actions/resolve-vocareum-aws/` |
| `resolve-aws-profile/action.yml` | `.github/actions/resolve-aws-profile/` |
| `ansible/` | **`deploy-pipeline/ansible/`** (keep this path) |
| [`docs/samples/.env.production`](samples/.env.production) | **`.env.production`** at the React repo root (`npm run build` / Vite) |

---

## 5. GitHub Environment `academy`

Create Environment **`academy`** on the portal repo. Do **not** point CD at CI Environments `integration` or `production`.

### Secrets (runner only — optional fallback)

Paste Vocareum AWS Details on each Run after Start Lab, **or** store these as Environment secrets. They change every session. Never put them on the EC2.

| Secret | When required |
| --- | --- |
| `AWS_ACCESS_KEY_ID` | If the Run form fields are empty |
| `AWS_SECRET_ACCESS_KEY` | If the Run form fields are empty |
| `AWS_SESSION_TOKEN` | If the Run form fields are empty |

### Variables (not secrets)

| Variable | Required? | Role |
| --- | --- | --- |
| `AWS_REGION` | Recommended | Defaults to `us-east-1` if empty |
| `PORTAL_IMAGE` | Required for `deploy` unless `image_ref` is set | Public GHCR or ECR tag. Empty is allowed for `configure-only` (stock `nginx`) |
| `IMAGE_HTTP_URL` | Optional | HTTPS or `s3://` CI `.tar.gz` for `docker load` |
| `VITE_STRIPE_PUBLISHABLE_KEY` | Optional | Academy **variable** (`pk_` only). Release bakes it; CD overlays guest `.env`. Never `sk_` |

Do **not** set `REST_BASE_URL`, `HAYSTACK_BASE_URL`, `VITE_*`, `VITE_API_TARGET`, Stripe `sk_` / `whsec_`, or `APP_CORS_*` on this Environment. They do not configure the React bundle. Same inventory as [`BOOTSTRAP.md`](BOOTSTRAP.md).

**Minimum `verify`:** Environment `academy` + three Vocareum keys + `AWS_REGION`.  
**Minimum `deploy`:** that, plus `PORTAL_IMAGE` or `image_ref` (or a tar **and** a matching tag). Stock nginx is forbidden on `deploy`.  
**Minimum `configure-only`:** academy + Vocareum keys + `AWS_REGION`. `PORTAL_IMAGE` optional (stock `nginx`). Guest `.env` must already exist in SM as `heavy-rental/portal` with `REST_BASE_URL`. Checkout `.env.api` is not read.

### Paid Environment `AWS_ACTUAL`

Create Environment **`AWS_ACTUAL`**. Variable `AWS_ROLE_TO_ASSUME`. **No** Vocareum `AWS_*` secrets. Same `PORTAL_IMAGE` / `AWS_REGION` names. Run **Web Portal CD (paid)** after infra paid `apply`. REST ALB is internet-facing `:8080`.

---

## 6. AWS (infra, not GitHub)

This CD does **not** create the ASG. Before any `deploy`:

1. Infra `action=apply` created `asg-portal` (public ALB `:80`).
2. Infra `aws-infra-academy.yml` `sync-secrets` filled **`heavy-rental/portal`** with `REST_BASE_URL=http://<rest_alb_dns>:8080` and Stripe `pk_`. REST SM separately gets `HAYSTACK_BASE_URL`, `APP_CORS_ALLOWED_ORIGINS=http://<portal_alb_dns>`, `sk_` / `whsec_`, JWT, RDS.
3. Guests are InService and SSM Online (Start Lab if the session ended). Desired=0 → infra, not this CD.

---

## 7. First CD run

Same sequence as [`BOOTSTRAP.md`](BOOTSTRAP.md) “Every run”:

1. Instructure → Start Lab → AWS Details.
2. Actions → **Web Portal CD (Academy)** → Environment `academy` → paste the three keys (or use Environment fallback).
3. `action=verify` — assert-lab + discover + SSM `GET /` on `:80` (`/api` down does not fail this job by itself).
4. `action=deploy` with a **new** public GHCR or ECR tag (or tar URL + matching tag). Stock nginx **forbidden**.
5. `action=configure-only` rewrites `/opt/heavy-rental/.env` from `heavy-rental/portal` and remounts nginx `/api` (stock nginx allowed). Does **not** rebuild the image, run `npm`, or read `.env.api`.

---

## 8. Do not

- Use CI Environments `integration` / `production` as CD
- Put Vocareum keys or Stripe `sk_` in the image, in `.env.production`, or on the Run form
- Bake `REST_BASE_URL` / `http://heavy-rental-rest-api:8080` / Haystack ALB / `localhost:8080` into the Vite bundle
- Expect GitHub `VITE_*` vars to reconfigure the running SPA
- Type instance IDs on the Run form
- Run `terraform apply` from this workflow
- Expect GHCR from a `develop` → `master` PR alone (publish a GitHub Release)
- Treat a green `verify` as proof that `/api` reached REST
