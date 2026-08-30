# Architecture Decision Records (portal pipelines)

Conflict order: **OpenSpec scenarios → OpenSPDD Safeguards → ADR → YAML**.

## CI family (`add-portal-ci-pipeline`)

| ID | Title |
| --- | --- |
| [0004](0004-portal-ci-reusable-caller.md) | Reusable workflows plus a sole-allowed caller; PR Integration Check reuses Fast Feedback (inlined pending-run jq) |
| [0005](0005-portal-ci-rest-tests-skip-clean.md) | REST endpoint tests skip cleanly until scripts exist |
| [0006](0006-portal-ci-stops-at-packaging.md) | CI family does not compose onto guests (Release still DAST + Publish) |
| [0007](0007-portal-ci-release-image-cloud-ready.md) | Release image is a static SPA; CD owns `/api` |
| [0008](0008-portal-vite-profile-vs-infra-estate.md) | Vite `.env.production` is a Release scan input (`--mode api` loads `.env.api`); REST hosts from AWS; GitHub `VITE_*` does not reconfigure the SPA |

## CD family (`add-portal-cd-academy-*`)

| ID | Title |
| --- | --- |
| [0001](0001-portal-cd-academy-only.md) | Portal app CD academy caller is Vocareum-only (paid is 0009) |
| [0009](0009-two-cd-actions-academy-paid.md) | Two portal CD Actions (academy / paid OIDC) |
| [0002](0002-vocareum-keys-masked.md) | Vocareum keys from the event payload, masked |
| [0003](0003-reuse-infra-portal-ansible.md) | Reuse infra portal Ansible (copy, do not fork) |
| [0008](0008-portal-vite-profile-vs-infra-estate.md) | Also CD: `/api` from SM; `pk_` overlay writes guest `.env` only; GitHub `VITE_*` does not reconfigure the SPA |
