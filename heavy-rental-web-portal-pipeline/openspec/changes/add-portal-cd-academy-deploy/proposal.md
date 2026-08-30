# Proposal: Portal CD Academy deploy (branch 2)

## Why

Branch 1 (`add-portal-cd-academy-skeleton`) could authenticate and see `asg-portal`. Operators still could not load a CI nginx image or refresh `/api` from this repo. At that time, infra `deploy-projects` was the only compose path (infra `apply` / `configure-only` do not compose portal).

## What Changes

- OpenSpec capabilities for resolve-image, portal-only Ansible, and `GET /` verify.
- Amend `portal-cd-scope`: deploy / configure-only no longer fail closed; still no Terraform.
- Copy infra `guest_base` + `portal` into `deploy-pipeline/ansible/` (do not invent a second compose). Guest nginx `/api` MUST match infra ADR 0018: no trailing URI, `Host $proxy_host`, omit `Origin`.
- `web-portal-cd-academy.yml`: `resolve-image` → `ansible-portal` → real `verify`.

## Capabilities

### New Capabilities

- `portal-cd-resolve-image`
- `portal-cd-ansible`
- `portal-cd-verify`

### Modified Capabilities

- `portal-cd-scope` — compose is allowed; Terraform and other ASG groups stay forbidden

## Impact

- Operators can `action=deploy` a public GHCR / ECR tag (or tar URL **and** a matching compose tag) onto both `asg-portal` guests.
- `action=configure-only` rewrites guest `.env` from `heavy-rental/portal` and remounts `/api` (omit `Origin`; the hairpin does not use Spring `APP_CORS_ALLOWED_ORIGINS`). It does not read `.env.api` or run `npm`. GitHub `academy` holds Vocareum keys, `PORTAL_IMAGE` / `IMAGE_HTTP_URL`, and optional `VITE_STRIPE_PUBLISHABLE_KEY` (`pk_` only — overlay writes guest `.env`; the SPA still uses the Release-baked key) (ADR 0008).
- `action=verify` is SSM `GET /` on `:80`, not discover-only.
- **Not in this change:** paid/OIDC, REST/Haystack/Neo4j groups, Terraform, `stop` / `destroy`.
