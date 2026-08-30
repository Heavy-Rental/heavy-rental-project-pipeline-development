# Architecture Decision Records (Haystack pipelines)

Conflict order: **OpenSpec scenarios → OpenSPDD Safeguards → ADR → YAML**.

## CI family (`add-haystack-ci-pipeline`)

| ID | Title |
| --- | --- |
| [0005](0005-haystack-ci-reusable-caller.md) | Reusable workflows plus a sole-allowed caller; Security Report is a separate pair (not a merge gate) |
| [0006](0006-haystack-ci-python-uv.md) | Toolchain is CPython 3.12 + uv |
| [0007](0007-haystack-ci-stops-at-packaging.md) | CI family does not compose onto guests (Release still DAST + Publish) |
| [0008](0008-haystack-ci-release-image-env-driven.md) | Estate from env; product defaults from sanitized `.env.prod` → `/app/.env` |
| [0009](0009-haystack-project-profile-vs-infra-estate.md) | Profile knobs on the Haystack project (guest overlay, not image); `NEO4J_URI` / `NEO4J_POPULATE_URL` from AWS |

## CD family (`add-haystack-cd-academy-*`, `add-haystack-cd-paid-deploy`, `add-haystack-cd-workers`)

| ID | Title |
| --- | --- |
| [0001](0001-haystack-cd-academy-only.md) | Haystack app CD academy caller is Vocareum-only (paid is 0010) |
| [0010](0010-two-cd-actions-academy-paid.md) | Two Haystack CD Actions (academy / paid OIDC) |
| [0002](0002-vocareum-keys-masked.md) | Vocareum keys from the event payload, masked |
| [0003](0003-reuse-infra-haystack-ansible.md) | Reuse infra Haystack Ansible (copy, do not fork) |
| [0004](0004-haystack-env-aliases-and-uv-sidecars.md) | App env aliases and Profile overlay (**sidecars amended** by 0011) |
| [0011](0011-devcontainer-worker-sidecars.md) | CD workers match estate: `sync-from-primary.sh` / `populate-neo4j-from-haystack.sh` |
| [0009](0009-haystack-project-profile-vs-infra-estate.md) | Also CD: academy / `AWS_ACTUAL` vars overlay guest `.env` only; they do not change GHCR |
