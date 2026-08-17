# Portal app CD (Academy) — branch 1 skeleton

This workflow discovers `asg-portal`. It does **not** pull GHCR or run Ansible yet.

Install from **`deploy-pipeline/`** into the React repo (same pattern as Release):

- `portal-cd-academy-caller.yml` → `.github/workflows/`
- `web-portal-cd-academy.yml` → `.github/workflows/`
- `resolve-vocareum-aws/action.yml` → `.github/actions/resolve-vocareum-aws/`

The pipeline-development monorepo root `.github/` mirrors those files so `HR-165` can dispatch here.

## GitHub Environment `academy`

Same **names** as infra CD (copy onto this repo):

- Optional fallback secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`
- Variable: `AWS_REGION` = `us-east-1`

Infra must already have applied the estate and `sync-secrets` (`heavy-rental/portal`).

## Every run

1. Start Lab → AWS Details.
2. Actions → **Web Portal CD (Academy)** → paste the three keys (or use Environment fallback).
3. Environment `academy`.
4. `action=verify` — assert + discover only (health is branch 2).
5. `action=deploy` / `configure-only` — fail closed until branch 2.

## Branch 2 (not this PR)

Yes — the **runner** still needs Vocareum keys (form or Environment `academy`) to call AWS (SSM, describe ASG). The **EC2** uses `LabRole`, not those keys.

CI already builds `ghcr.io/<owner>/heavy-rental-web-portal:<tag>` on non-PR Release and a docker tar artifact. Public GHCR can be pulled later without a GitHub token on the guest.
