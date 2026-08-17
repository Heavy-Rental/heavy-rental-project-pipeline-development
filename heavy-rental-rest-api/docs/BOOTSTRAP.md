# REST app CD (Academy)

This workflow discovers `asg-rest` and can re-run REST compose (branch 2). It does **not** run Terraform or create the ASG.

Installing Release + CD into [heavy-rental-spring-rest-api](https://github.com/Heavy-Rental/heavy-rental-spring-rest-api): [`PREPARE-SPRING-REPO.md`](PREPARE-SPRING-REPO.md).

Install from **`deploy-pipeline/`** into the Spring repo (same pattern as Release):

- `rest-api-cd-academy-caller.yml` → `.github/workflows/`
- `rest-api-cd-academy.yml` → `.github/workflows/`
- `resolve-vocareum-aws/action.yml` → `.github/actions/resolve-vocareum-aws/`
- **`ansible/`** → `deploy-pipeline/ansible/` (keep this path; the reusable workflow uses `working-directory: deploy-pipeline/ansible`)

## GitHub Environment `academy`

Same **names** as infra CD (copy onto this repo):

- Optional fallback secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`
- Variable: `AWS_REGION` = `us-east-1`
- Variable: `REST_IMAGE` — registry tag (public GHCR or ECR). **Required** for `deploy` / `configure-only` unless `image_ref` / `image_http_url` is set. There is no stock Tomcat.
- Optional variable: `IMAGE_HTTP_URL` — HTTPS or `s3://` CI tar for `docker load`

Do **not** point this workflow at CI Environments `integration` or `production`. Infra must already have applied the estate and `sync-secrets` (`heavy-rental/rest`).

## Every run

1. Start Lab → AWS Details.
2. Actions → **REST API CD (Academy)** → paste the three keys (or use Environment fallback).
3. Environment `academy`.
4. `action=verify` — assert + discover + SSM `GET :8080` (does not fail solely because Haystack is down).
5. `action=configure-only` — refresh `.env` with current `REST_IMAGE` or `image_ref` (fails if both empty).
6. `action=deploy` — `image_ref` or `REST_IMAGE` (or `image_http_url` tar). Prefer a **new tag**. Public GHCR: no login. ECR: guest `LabRole`. Private GHCR fails (copy to ECR or use a tar).

The **runner** still needs Vocareum keys. The **EC2** uses `LabRole`, not those keys.

CI already builds `ghcr.io/<owner>/heavy-rental-rest-api:<tag>` on non-PR Release and a docker tar artifact.
