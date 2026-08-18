# Proposal: Portal CD Academy deploy (branch 2)

## Why

Branch 1 (`add-portal-cd-academy-skeleton`) can authenticate and see `asg-portal`. Operators still cannot load a CI nginx image or refresh `/api` from this repo. Infra `configure-only` + `PORTAL_IMAGE` is the only compose path.

## What Changes

- OpenSpec capabilities for resolve-image, portal-only Ansible, and `GET /` verify.
- Amend `portal-cd-scope`: deploy / configure-only no longer fail closed; still no Terraform.
- Copy infra `guest_base` + `portal` into `deploy-pipeline/ansible/` (do not invent a second compose).
- `web-portal-cd-academy.yml`: `resolve-image` → `ansible-portal` → real `verify`.

## Capabilities

### New Capabilities

- `portal-cd-resolve-image`
- `portal-cd-ansible`
- `portal-cd-verify`

### Modified Capabilities

- `portal-cd-scope` — compose is allowed; Terraform and other ASG groups stay forbidden

## Impact

- Operators can `action=deploy` a public GHCR / ECR tag (or tar URL) onto both `asg-portal` guests.
- `action=configure-only` rewrites guest `.env` from `heavy-rental/portal` and remounts `/api`. It does not read `.env.api` or run `npm`. GitHub academy holds Vocareum keys and `PORTAL_IMAGE` only (ADR 0008).
- `action=verify` is SSM `GET /` on `:80`, not discover-only.
- **Not in this change:** paid/OIDC, REST/Haystack/Neo4j groups, Terraform, `stop` / `destroy`.
