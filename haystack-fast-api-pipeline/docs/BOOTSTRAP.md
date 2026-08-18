# Haystack app CD (Academy)

This workflow discovers `asg-haystack` and can re-run Haystack compose (branch 2). It does **not** run Terraform or create the ASG. It does **not** start Neo4j.

Specification index: [`../specification/README.md`](../specification/README.md). CD walkthrough: [`../specification/pipelines/haystack-cd.md`](../specification/pipelines/haystack-cd.md).

**App repo is not ready yet.** Checklist and env/sidecar gaps: [`PREPARE-HAYSTACK-REPO.md`](PREPARE-HAYSTACK-REPO.md).

Install from **`deploy-pipeline/`** into the Haystack app repo (same pattern as Release):

- `haystack-cd-academy-caller.yml` → `.github/workflows/`
- `haystack-cd-academy.yml` → `.github/workflows/`
- `resolve-vocareum-aws/action.yml` → `.github/actions/resolve-vocareum-aws/`
- **`ansible/`** → `deploy-pipeline/ansible/` (keep this path)

## GitHub Environment `academy`

- Optional fallback secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`
- Variable: `AWS_REGION` = `us-east-1`
- Variable: `HAYSTACK_IMAGE` — public GHCR or ECR tag. **Required** for `deploy` / `configure-only` unless `image_ref` is set. No stock uvicorn.
- Optional: `IMAGE_HTTP_URL` — HTTPS or `s3://` CI tar

Infra must already have applied the estate and `sync-secrets` (`heavy-rental/haystack`).

## Every run

1. Start Lab → AWS Details.
2. Actions → **Haystack CD (Academy)** → Environment `academy` → paste Vocareum keys (or Environment fallback).
3. `action=verify` — assert + discover + SSM `GET :8000/docs` or `/health`.
4. `action=configure-only` — refresh `.env` from `heavy-rental/haystack`, add app aliases / live flags if missing; needs `HAYSTACK_IMAGE` or `image_ref`.
5. `action=deploy` — new public GHCR/ECR tag (or tar). Prefer a **new tag**. Sidecar crash-loops do not fail `verify` if uvicorn answers.

The **runner** uses Vocareum keys. The **EC2** uses `LabRole`.
