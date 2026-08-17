# Proposal: Haystack CD Academy deploy (branch 2)

## Why

Branch 1 can see `asg-haystack` but cannot load a CI uvicorn image. Infra `configure-only` no longer composes Haystack. There is no Haystack-only image path until this change.

## What Changes

- OpenSpec for resolve-image, haystack-only Ansible, and `:8000` verify.
- Amend `haystack-cd-scope`: compose allowed; no Terraform; no neo4j service.
- Copy infra `guest_base` + `haystack` into `deploy-pipeline/ansible/`.
- `haystack-cd-academy.yml`: resolve-image → ansible-haystack → real verify.

## Capabilities

### New Capabilities

- `haystack-cd-resolve-image`
- `haystack-cd-ansible`
- `haystack-cd-verify`

### Modified Capabilities

- `haystack-cd-scope`

## Impact

- `action=deploy` updates both `asg-haystack` guests. Sync + populate stay; no Neo4j container.
- **Not in this change:** paid/OIDC, portal/REST/Neo4j groups, Terraform.
