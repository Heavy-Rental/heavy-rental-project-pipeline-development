# REST app CD (Academy + paid)

This workflow discovers `asg-rest` and can re-run REST compose (branch 2). It does **not** run Terraform or create the ASG. The Release image is env-only (ADR 0007); this CD injects `heavy-rental/rest` and must not expect JDBC inside the image.

Specification index: [`../specification/README.md`](../specification/README.md). CD walkthrough: [`../specification/pipelines/rest-cd.md`](../specification/pipelines/rest-cd.md).

Installing Release + CD into [heavy-rental-spring-rest-api](https://github.com/Heavy-Rental/heavy-rental-spring-rest-api): [`PREPARE-SPRING-REPO.md`](PREPARE-SPRING-REPO.md).

Install from **`deploy-pipeline/`** into the Spring repo (same pattern as Release):

- `rest-api-cd-academy-caller.yml` → `.github/workflows/`
- `rest-api-cd-paid-caller.yml` → `.github/workflows/` (billed AWS)
- `rest-api-cd-academy.yml` → `.github/workflows/` (shared jobs)
- `resolve-aws-profile/action.yml` → `.github/actions/resolve-aws-profile/`
- **`ansible/`** → `deploy-pipeline/ansible/` (keep this path; the reusable workflow uses `working-directory: deploy-pipeline/ansible`)

Do **not** copy `resolve-vocareum-aws/` (REST CD does not `uses:` it; `resolve-aws-profile` already masks Vocareum keys).

## GitHub Environment `academy`

Same **names** as infra CD (copy onto this repo):

- Optional fallback secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`
- Variable: `AWS_REGION` = `us-east-1`
- Variable: `REST_IMAGE` — registry tag (public GHCR or ECR). **Required** for `deploy` / `configure-only` unless `image_ref` is set. There is no stock Tomcat. `image_http_url` / `IMAGE_HTTP_URL` is optional **in addition** (tar for `docker load`) and still needs a matching compose tag.
- Optional variable: `IMAGE_HTTP_URL` — HTTPS or `s3://` CI tar for `docker load` (does **not** replace `REST_IMAGE` / `image_ref`)
- Optional pricing variables (empty = SM / Spring defaults): `DYNAMIC_PRICING_ENABLED`, `PRICING_DEFAULT_DISTANCE_KM`, `PRICING_ORIGIN_POSTAL_CODE`, `PRICING_DISTANCE_LOOKUP_ENABLED`

Do **not** point this workflow at CI Environment `integration`. Infra must already have applied the estate and `sync-secrets` (`heavy-rental/rest`). Infra `apply` does **not** compose REST; first compose is infra `deploy-projects` or this CD `action=deploy`.

## GitHub Environment `AWS_ACTUAL` (paid)

Create Environment **`AWS_ACTUAL`**. Variable `AWS_ROLE_TO_ASSUME` (OIDC). Same `REST_IMAGE` / pricing vars. **No** `AWS_ACCESS_KEY_ID`. Run **REST API CD (paid)** after infra **AWS infrastructure (paid)** `apply`. Guests use `hr-paid-rest`. Ansible SSM uses `heavy-rental-ssm-<account>-actual`. REST ALB is internet-facing `:8080`.

## Every run

Academy:

1. Start Lab → AWS Details.
2. Actions → **REST API CD (Academy)** → paste the three keys (or use Environment fallback).
3. Environment `academy`.
4. `action=verify` — assert + discover + SSM `GET :8080/actuator/health` must be **2xx** (same as ALB `tg-rest` matcher `200-299`). Spring 401 on `/` is not healthy. Does not fail solely because Haystack is down.
5. `action=configure-only` — refresh `.env` with current `REST_IMAGE` or `image_ref` (fails if both empty). Optional tar URL still needs that matching tag.
6. `action=deploy` — `image_ref` or `REST_IMAGE`, optionally plus `image_http_url` tar. Prefer a **new tag**. Public GHCR: no login. ECR: guest `LabRole`. Private GHCR fails (copy to ECR or use a tar **and** a matching tag).

Paid: Actions → **REST API CD (paid)** → Environment `AWS_ACTUAL`. No Vocareum keys. Same `verify` / `configure-only` / `deploy` actions and the same image-tag rule.

On academy, the **runner** still needs Vocareum keys; the **EC2** uses `LabRole`, not those keys. On paid, the runner uses OIDC; the **EC2** uses `hr-paid-rest`.

Release `workflow_dispatch` Publish pushes `ghcr.io/<owner>/heavy_rental_rest_api:<x.y.z>` and `:latest` and uploads `heavy_rental_rest_api-image.tar.gz`.
