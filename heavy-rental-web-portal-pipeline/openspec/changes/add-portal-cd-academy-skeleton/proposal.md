# Proposal: Portal CD Academy skeleton (`HR-165`)

**As-built:** Compose is delivered (`add-portal-cd-academy-deploy`). First-compose is infra `deploy-projects` (`site.yml`) or this app CD (not infra `apply`). GHCR is Release Publish on `workflow_dispatch` only. Keep this file as the branch-1 record.

## Why

Infra CD already creates `asg-portal`. Portal CI already builds `nginx` + `dist/` and pushes GHCR (dispatch-only Publish) plus a Release tar. There is no portal **app CD** workflow that can authenticate to Vocareum and discover those guests without Terraform.

## What Changes

- OpenSpec, OpenSPDD, ADRs 0001–0002.
- `.github/workflows/web-portal-cd-academy.yml`: `assert-lab` + `discover-targets`.
- `deploy` / `configure-only` compose fail closed (branch 2). **Superseded** by `add-portal-cd-academy-deploy`.

## Capabilities

### New Capabilities

- `portal-cd-academy-auth`
- `portal-cd-discover`
- `portal-cd-scope`

## Impact

- Operators create GitHub Environment `academy` on this repo (same secret **names** as infra).
- **Not in this change:** Ansible compose, image pull, paid/OIDC, Terraform.
