# Prepare the React portal for Academy CD

**App repo:** [Heavy-Rental/heavy-rental-react-web-portal](https://github.com/Heavy-Rental/heavy-rental-react-web-portal)  
**Release CI:** `release-pipeline/` in this tree (copy into the app repo `.github/workflows/`)  
**App CD:** `deploy-pipeline/` (this tree — copy when ready)  
**Estate:** infra `apply` + `sync-secrets` must have created `asg-portal` and `heavy-rental/portal`

This file is the operator checklist. It does not apply Terraform or push images.

Everyday operate after install: [`BOOTSTRAP.md`](BOOTSTRAP.md). Specification: [`../specification/pipelines/portal-cd.md`](../specification/pipelines/portal-cd.md).

---

## 1. Can Release build the image CD expects?

**Yes, when Release runs in the app repo.** The SPA matches the packaging contract.

| App | Release / CD contract |
| --- | --- |
| Node **22**, `package-lock.json`, Vite `npm run build` | `dist/index.html` + hashed JS/CSS |
| Static SPA | `nginx:1.27-alpine` serving `dist/` (try_files only). CD **replaces** `default.conf` with `/api` → `REST_BASE_URL` |
| No app `Dockerfile` required | Release generates the nginx image |
| Same-origin `/api` | Release `npm run build` must **not** inline `localhost:8080` / lab REST URLs or `sk_` |

Packaging scans `dist/` and the image html tree for `sk_`, AWS secret material, JDBC URLs, and `localhost:8080`/`8000`. Stripe `pk_` is allowed. Generated nginx has no `proxy_pass` host.

GHCR name: `ghcr.io/<owner>/heavy_rental_web_portal` (lowercase). On `Heavy-Rental` that is `ghcr.io/heavy-rental/heavy_rental_web_portal:<x.y.z>` and `:latest`. The version tag is the previous GHCR semver with the patch bumped (first publish is `1.0.0`).

| Release trigger | What you get |
| --- | --- |
| PR `develop` → `master` | `dist/` zip + docker **tar artifact**. **No GHCR push.** |
| **Published GitHub Release** | Tar **and** GHCR `<version>` + `:latest` |

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

Optional Academy path: upload the Release tar to lab S3 and set `IMAGE_HTTP_URL` / `image_http_url`. You still need a compose tag that matches the loaded image name (`PORTAL_IMAGE` or `image_ref`).

---

## 4. Install portal app CD into the React repo

Copy from this tree’s `deploy-pipeline/`:

| Source | Destination in the React repo |
| --- | --- |
| `portal-cd-academy-caller.yml` | `.github/workflows/` |
| `web-portal-cd-academy.yml` | `.github/workflows/` |
| `resolve-vocareum-aws/action.yml` | `.github/actions/resolve-vocareum-aws/` |
| `ansible/` | **`deploy-pipeline/ansible/`** (keep this path) |

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

**Minimum `verify`:** Environment `academy` + three Vocareum keys + `AWS_REGION`.  
**Minimum `deploy`:** that, plus `PORTAL_IMAGE` or `image_ref` (or a tar **and** a matching tag). Stock nginx is forbidden on `deploy`.

---

## 6. AWS (infra, not GitHub)

This CD does **not** create the ASG. Before any `deploy`:

1. Infra `action=apply` created `asg-portal` (public ALB `:80`).
2. Infra `sync-secrets` filled **`heavy-rental/portal`** with `REST_BASE_URL` + Stripe `pk_`.
3. Guests are InService and SSM Online (Start Lab if the session ended). Desired=0 → infra, not this CD.

---

## 7. First CD run

1. Instructure → Start Lab → AWS Details.
2. Actions → **Web Portal CD (Academy)** → Environment `academy` → paste the three keys (or use Environment fallback).
3. `action=verify` — assert-lab + discover + SSM `GET /` on `:80` (`/api` down does not fail this job by itself).
4. `action=deploy` with a **new** public GHCR or ECR tag (or tar URL + matching tag).
5. `action=configure-only` refreshes `.env` + `/api` (stock nginx allowed).

---

## 8. Do not

- Use CI Environments `integration` / `production` as CD
- Put Vocareum keys or `sk_` in the image
- Type instance IDs on the Run form
- Run `terraform apply` from this workflow
- Expect GHCR from a `develop`→`master` PR alone
- Treat a green `verify` as proof that `/api` reached REST
