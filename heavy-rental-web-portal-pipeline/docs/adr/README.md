# Architecture Decision Records (portal pipelines)

Conflict order: **OpenSpec → OpenSPDD → ADR → YAML**.

## CI family (`add-portal-ci-pipeline`)

| ID | Title |
| --- | --- |
| [0004](0004-portal-ci-reusable-caller.md) | Reusable workflows plus a sole-allowed caller |
| [0005](0005-portal-ci-rest-tests-skip-clean.md) | REST endpoint tests skip cleanly until scripts exist |
| [0006](0006-portal-ci-stops-at-packaging.md) | CI family stops at packaging |
| [0007](0007-portal-ci-release-image-cloud-ready.md) | Release image is a static SPA; CD owns `/api` |

## CD family (`add-portal-cd-academy-*`)

| ID | Title |
| --- | --- |
| [0001](0001-portal-cd-academy-only.md) | Portal app CD is Academy / Vocareum first |
| [0002](0002-vocareum-keys-masked.md) | Vocareum keys from the event payload, masked |
| [0003](0003-reuse-infra-portal-ansible.md) | Reuse infra portal Ansible (copy, do not fork) |
