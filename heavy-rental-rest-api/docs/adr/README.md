# Architecture Decision Records (REST pipelines)

Conflict order: **OpenSpec → OpenSPDD → ADR → YAML**.

## CI family (`add-rest-ci-pipeline`)

| ID | Title |
| --- | --- |
| [0004](0004-rest-ci-reusable-caller.md) | Reusable workflows plus a sole-allowed caller |
| [0005](0005-rest-ci-secret-environments.md) | Integration vs Release `REST_API_DB_*` Environments |
| [0006](0006-rest-ci-stops-at-packaging.md) | CI family stops at packaging |
| [0007](0007-rest-ci-release-image-env-driven.md) | Release image takes guest config from the environment |

## CD family (`add-rest-cd-academy-*`)

| ID | Title |
| --- | --- |
| [0001](0001-rest-cd-academy-only.md) | REST app CD academy caller is Vocareum-only (paid is 0008) |
| [0008](0008-two-cd-actions-academy-paid.md) | Two REST CD Actions (academy / paid OIDC) |
| [0002](0002-vocareum-keys-masked.md) | Vocareum keys from the event payload, masked |
| [0003](0003-reuse-infra-rest-ansible.md) | Reuse infra REST Ansible (copy, do not fork) |
