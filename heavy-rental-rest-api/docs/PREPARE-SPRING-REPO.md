# Prepare heavy-rental-spring-rest-api for Academy CD

**App repo:** [Heavy-Rental/heavy-rental-spring-rest-api](https://github.com/Heavy-Rental/heavy-rental-spring-rest-api)  
**Release CI:** `release-pipeline/` (already copied into the app repo `.github/workflows/` on `develop`)  
**App CD:** `deploy-pipeline/` (this tree — **not** in the app repo yet)  
**Estate:** infra `apply` + `sync-secrets` must have created `asg-rest` and `heavy-rental/rest`

This file is the operator checklist. It does not apply Terraform or push images.

Specification: [`../specification/README.md`](../specification/README.md). CD walkthrough: [`../specification/pipelines/rest-cd.md`](../specification/pipelines/rest-cd.md).

---

## 1. Can Release build the image CD expects?

**Yes.** The live app matches the Release packaging contract.

| App (`develop`) | Release / CD contract |
| --- | --- |
| Java **21**, `packaging=war`, Tomcat `provided` | `tomcat:10.1-jdk21-temurin` + `ROOT.war` (not a fat JAR / `java -jar` image) |
| `server.port=8080`, Actuator on the classpath | Health `GET :8080/actuator/health` or `/` |
| App `Dockerfile` ignored | Release **always** generates the Tomcat + WAR image. Runnable with `docker run -p 8080:8080 -e …` (Docker Desktop or any Engine) |

Generated image (app Dockerfile is ignored):

```dockerfile
# Runtime env from docker -e / compose env_file (do not ENV/ARG these):
#   POSTGRES_*, SPRING_DATASOURCE_*, HAYSTACK_BASE_URL, STRIPE_*, APP_JWT_SECRET
FROM tomcat:10.1-jdk21-temurin
COPY target/*.war /usr/local/tomcat/webapps/ROOT.war
EXPOSE 8080
CMD ["catalina.sh", "run"]
```

Desktop / any Engine: `docker run -p 8080:8080 -e SPRING_DATASOURCE_URL=… ghcr.io/<owner>/heavy_rental_rest_api:<tag>`

Packaging fails if the generated Dockerfile bakes `ENV`/`ARG` for those keys or copies a `.env`. After build it proves dummy `SPRING_DATASOURCE_URL` / `POSTGRES_HOST` / `HAYSTACK_BASE_URL` / Stripe / JWT are visible, confirms `ROOT.war` has `WEB-INF/`, and starts Tomcat only to prove `:8080` binds. It does not connect to RDS. `spring-datasource.env` is a Release artifact (no password) and is **not** copied into the image.

GHCR name: `ghcr.io/<owner>/heavy_rental_rest_api` (lowercase). On `Heavy-Rental` that is `ghcr.io/heavy-rental/heavy_rental_rest_api:<x.y.z>` and `:latest`. The version tag is the previous GHCR semver with the patch bumped (first publish is `1.0.0`).

| Release trigger | What you get |
| --- | --- |
| PR `develop` → `master` | Versioned WAR + docker **tar artifact**. **No GHCR push.** |
| **Published GitHub Release** | Tar **and** GHCR `<version>` + `:latest` |

Academy guests pull **public** GHCR with no token. A PR build is not enough for `REST_IMAGE=ghcr.io/…` unless you `docker load` the tar (`image_http_url` / `IMAGE_HTTP_URL`) or copy the image to ECR.

`DEFAULT_APP_REPOSITORY: SA62-team1/…` in the reusable YAML is only for local `act`. When Release runs **in** `heavy-rental-spring-rest-api`, checkout is the calling repo (into `app/`). That is correct.

---

## 2. Already on the app repo vs still to copy

On app `develop` today:

- Present: `rest-api-release-caller.yml`, `release-pipeline.yml`, Fast Feedback, Integration
- **Missing:** `deploy-pipeline/` (CD caller, reusable workflow, `resolve-vocareum-aws`, `ansible/`)

---

## 3. Produce a pullable image

1. CI Environment **`production`** (Release QC only) has `REST_API_CLOUD_DB_*` if QC is not already green. Those names are **not** CD and **not** what the guest reads.
2. Merge to `master` and **publish a GitHub Release**. That is what pushes GHCR.
3. Org Packages → `heavy_rental_rest_api` → visibility **Public**. Private GHCR fails CD on purpose (no PAT on the guest).
4. Record the tag, for example `ghcr.io/heavy-rental/heavy_rental_rest_api:1.0.0` (or `:latest`). Prefer a **new** version tag each deploy (`compose up` is not `--pull always`).

Optional Academy path: upload the Release tar to lab S3 and set `IMAGE_HTTP_URL` / `image_http_url` (`s3://` or HTTPS). You still need a compose tag that matches the loaded image name (`REST_IMAGE` or `image_ref`).

---

## 4. Install REST app CD into the Spring repo

Copy from this tree’s `deploy-pipeline/`:

| Source | Destination in the Spring repo |
| --- | --- |
| `rest-api-cd-academy-caller.yml` | `.github/workflows/` |
| `rest-api-cd-academy.yml` | `.github/workflows/` |
| `resolve-vocareum-aws/action.yml` | `.github/actions/resolve-vocareum-aws/` |
| `ansible/` | **`deploy-pipeline/ansible/`** (keep this path) |

Everyday operate: [`BOOTSTRAP.md`](BOOTSTRAP.md).

---

## 5. GitHub Environment `academy`

Create Environment **`academy`** on the Spring repo. Do **not** point CD at CI Environments `integration` or `production`.

### Secrets (runner only — optional fallback)

Paste Vocareum AWS Details on each Run after Start Lab, **or** store these as Environment secrets. They change every session. Never put them on the EC2 or in AWS Secrets Manager.

| Secret | When required |
| --- | --- |
| `AWS_ACCESS_KEY_ID` | If the Run form fields are empty |
| `AWS_SECRET_ACCESS_KEY` | If the Run form fields are empty |
| `AWS_SESSION_TOKEN` | If the Run form fields are empty |

### Variables (not secrets)

| Variable | Required? | Role |
| --- | --- | --- |
| `AWS_REGION` | Recommended | Defaults to `us-east-1` if empty |
| `REST_IMAGE` | Required for `deploy` / `configure-only` unless `image_ref` is set | Public GHCR or ECR tag. No stock Tomcat. |
| `IMAGE_HTTP_URL` | Optional | HTTPS or `s3://` CI `.tar.gz` for `docker load` |

### Run form

| Input | Use |
| --- | --- |
| `aws_environment` | Must be **`academy`** |
| `aws_access_key_id` / `aws_secret_access_key` / `aws_session_token` | Fresh Vocareum keys (override Environment secrets) |
| `image_ref` | One-off tag if `REST_IMAGE` is empty |
| `image_http_url` | One-off tar if `IMAGE_HTTP_URL` is empty |

**Minimum `verify`:** Environment `academy` + three Vocareum keys + `AWS_REGION`.  
**Minimum `deploy` / `configure-only`:** that, plus `REST_IMAGE` or `image_ref` (or a tar **and** a matching tag).

---

## 6. AWS (infra, not GitHub)

This CD does **not** create the ASG. Before any `deploy`:

1. Infra `action=apply` created `asg-rest` (internal ALB `:8080`).
2. Infra `sync-secrets` filled **`heavy-rental/rest`**.
3. Guests are InService and SSM Online (Start Lab if the session ended). Desired=0 → infra, not this CD.

The guest (`LabRole`) reads `heavy-rental/rest`. CI `REST_API_CLOUD_DB_*` is never copied onto the instance.

---

## 7. Runtime env names (image can be right; keys may not)

`application.properties` in the Spring repo does **not** use every name the estate study lists. Stripe names match. These do not:

| App reads | `heavy-rental/rest` after this patch |
| --- | --- |
| `POSTGRES_HOSTNAME` | written (same value as `POSTGRES_HOST`) |
| `POSTGRES_DB` | written (same value as `POSTGRES_DATABASE`) |
| `POSTGRES_USER` | written (same value as `POSTGRES_USERNAME`) |
| `POSTGRES_PASSWORD` / `POSTGRES_PORT` | written |
| `HAYSTACK_BASE_URL` | written (internal Haystack ALB). Estate no longer uses `HAYSTACK_URL` |
| `APP_JWT_SECRET` (≥ 32 characters) | **not** written — set in SM or the app keeps the insecure default |
| `APP_CORS_ALLOWED_ORIGINS` | **not** written — portal `/api` is same-origin |
| `STRIPE_API_KEY` / `STRIPE_WEBHOOK_SECRET` / `STRIPE_PUBLISHABLE_KEY` | written |

Re-run infra `configure-only` after this patch so guests get a new `.env`. `APP_JWT_SECRET` is still a separate follow-up.

---

## 8. First CD run

1. Instructure → Start Lab → AWS Details.
2. Actions → **REST API CD (Academy)** → Environment `academy` → paste the three keys (or use Environment fallback).
3. `action=verify` — assert-lab + discover + SSM `GET :8080` (Haystack down does not fail this job by itself).
4. `action=deploy` with a **new** public GHCR or ECR tag (or tar URL + matching tag).
5. `action=configure-only` refreshes `.env` from `heavy-rental/rest` (still needs `REST_IMAGE` or `image_ref` — no stock Tomcat).

---

## 9. Do not

- Use CI Environments `integration` / `production` as CD
- Treat `REST_API_CLOUD_DB_*` as the guest database config
- Put Vocareum keys or `sk_` in the image
- Type instance IDs on the Run form
- Run `terraform apply` from this workflow
- Expect GHCR from a `develop`→`master` PR alone
