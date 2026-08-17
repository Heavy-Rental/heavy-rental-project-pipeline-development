# Haystack app CD (Academy) — branch 1 skeleton

This workflow discovers `asg-haystack`. It does **not** pull GHCR or run Ansible yet.

Install from **`deploy-pipeline/`** into the Haystack app repo (same pattern as Release):

- `haystack-cd-academy-caller.yml` → `.github/workflows/`
- `haystack-cd-academy.yml` → `.github/workflows/`
- `resolve-vocareum-aws/action.yml` → `.github/actions/resolve-vocareum-aws/`

## GitHub Environment `academy`

Same **names** as infra CD (copy onto this repo):

- Optional fallback secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`
- Variable: `AWS_REGION` = `us-east-1`

Infra must already have applied the estate and `sync-secrets` (`heavy-rental/haystack`).

## Every run

1. Start Lab → AWS Details.
2. Actions → **Haystack CD (Academy)** → paste the three keys (or use Environment fallback).
3. Environment `academy`.
4. `action=verify` — assert + discover only (health is branch 2).
5. `action=deploy` / `configure-only` — fail closed until branch 2.

The **runner** still needs Vocareum keys. The **EC2** uses `LabRole`, not those keys.

CI already builds `ghcr.io/<owner>/haystack-fast-api:<tag>` on non-PR Release and a docker tar artifact.
