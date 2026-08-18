# Portal app CD (Academy)

This workflow discovers `asg-portal` and can re-run portal compose (branch 2). It does **not** run Terraform or create the ASG. The Release image is a static SPA (ADR 0007); this CD mounts nginx `/api` → `REST_BASE_URL`.

Specification index: [`../specification/README.md`](../specification/README.md). CD walkthrough: [`../specification/pipelines/portal-cd.md`](../specification/pipelines/portal-cd.md). App-repo checklist: [`PREPARE-PORTAL-REPO.md`](PREPARE-PORTAL-REPO.md).

Install from **`deploy-pipeline/`** into the React repo (same pattern as Release):

- `portal-cd-academy-caller.yml` → `.github/workflows/`
- `web-portal-cd-academy.yml` → `.github/workflows/`
- `resolve-vocareum-aws/action.yml` → `.github/actions/resolve-vocareum-aws/`
- **`ansible/`** → `deploy-pipeline/ansible/` (keep this path; the reusable workflow uses `working-directory: deploy-pipeline/ansible`)

## GitHub Environment `academy`

Same **names** as infra CD (copy onto this repo):

- Optional fallback secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`
- Variable: `AWS_REGION` = `us-east-1`
- Variable: `PORTAL_IMAGE` — registry tag (public GHCR or ECR). Empty is allowed for `configure-only` (stock `nginx`) and forbidden for `action=deploy` unless `image_ref` / `image_http_url` is set
- Optional variable: `IMAGE_HTTP_URL` — HTTPS or `s3://` CI tar for `docker load`

Infra must already have applied the estate and `sync-secrets` (`heavy-rental/portal` with `REST_BASE_URL` + `pk_`).

## Every run

1. Start Lab → AWS Details.
2. Actions → **Web Portal CD (Academy)** → paste the three keys (or use Environment fallback).
3. Environment `academy`.
4. `action=verify` — assert + discover + SSM `GET /` on `:80` (does not fail solely because `/api` is down).
5. `action=configure-only` — refresh `.env` + `/api` with current `PORTAL_IMAGE` or stock `nginx`.
6. `action=deploy` — `image_ref` or `PORTAL_IMAGE` (or `image_http_url` tar). Prefer a **new tag**. Public GHCR: no login. ECR: guest `LabRole`. Private GHCR fails (copy to ECR or use a tar).

The **runner** still needs Vocareum keys (form or Environment `academy`) to call AWS. The **EC2** uses `LabRole`, not those keys.

CI already builds `ghcr.io/<owner>/heavy_rental_web_portal:<x.y.z>` and `:latest` on non-PR Release and a docker tar artifact. Public GHCR can be pulled without a GitHub token on the guest.
