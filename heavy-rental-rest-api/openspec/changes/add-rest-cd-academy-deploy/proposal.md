# Proposal: REST CD Academy deploy (branch 2)

## Why

Branch 1 (`add-rest-cd-academy-skeleton`) can authenticate and see `asg-rest`. Operators still cannot load a CI Tomcat image or refresh `.env` from this repo. Infra `configure-only` + `REST_IMAGE` is the only compose path.

## What Changes

- OpenSpec capabilities for resolve-image, rest-only Ansible, and `:8080` verify.
- Amend `rest-cd-scope`: deploy / configure-only no longer fail closed; still no Terraform.
- Copy infra `guest_base` + `rest` into `deploy-pipeline/ansible/`.
- `rest-api-cd-academy.yml`: `resolve-image` → `ansible-rest` → real `verify`.

## Capabilities

### New Capabilities

- `rest-cd-resolve-image`
- `rest-cd-ansible`
- `rest-cd-verify`

### Modified Capabilities

- `rest-cd-scope` — compose is allowed; Terraform and other ASG groups stay forbidden

## Impact

- Operators can `action=deploy` a public GHCR / ECR tag (or tar URL) onto both `asg-rest` guests.
- `action=configure-only` refreshes `heavy-rental/rest` without inventing a Tomcat tag.
- `action=verify` is SSM `GET :8080/actuator/health` (**2xx**; same as ALB `tg-rest`), not discover-only.
- **Not in this change:** paid/OIDC, portal/Haystack/Neo4j groups, Terraform, `stop` / `destroy`.
