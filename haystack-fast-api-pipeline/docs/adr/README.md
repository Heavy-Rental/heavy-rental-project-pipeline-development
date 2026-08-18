# Architecture Decision Records (Haystack pipelines)

Conflict order: **OpenSpec → OpenSPDD → ADR → YAML**.

## CI family (`add-haystack-ci-pipeline`)

| ID | Title |
| --- | --- |
| [0005](0005-haystack-ci-reusable-caller.md) | Reusable workflows plus a sole-allowed caller |
| [0006](0006-haystack-ci-python-uv.md) | Toolchain is CPython 3.12 + uv |
| [0007](0007-haystack-ci-stops-at-packaging.md) | CI family stops at packaging |
| [0008](0008-haystack-ci-release-image-env-driven.md) | Release image takes DB and sync config from the environment |

## CD family (`add-haystack-cd-academy-*`)

| ID | Title |
| --- | --- |
| [0001](0001-haystack-cd-academy-only.md) | Haystack app CD is Academy / Vocareum first |
| [0002](0002-vocareum-keys-masked.md) | Vocareum keys from the event payload, masked |
| [0003](0003-reuse-infra-haystack-ansible.md) | Reuse infra Haystack Ansible (copy, do not fork) |
| [0004](0004-haystack-env-aliases-and-uv-sidecars.md) | App env aliases and uv sidecar commands |
