# Proposal: Haystack CD Academy skeleton

## Why

Infra CD already creates `asg-haystack` and first-composes uvicorn + sync + populate. Haystack CI already builds `python:3.12-slim-bookworm` + uvicorn; Release Publish pushes public GHCR plus a Release tar. There is no Haystack **app CD** workflow that can authenticate to Vocareum and discover those guests without Terraform.

## What Changes

- OpenSpec, OpenSPDD, ADRs 0001–0002, BOOTSTRAP.
- `deploy-pipeline/haystack-cd-academy.yml`: `assert-lab` + `discover-targets`.
- `deploy` / `configure-only` compose fail closed (branch 2).

## Capabilities

### New Capabilities

- `haystack-cd-academy-auth`
- `haystack-cd-discover`
- `haystack-cd-scope`

## Impact

- Operators create GitHub Environment `academy` on this repo (same secret **names** as infra).
- **Not in this change:** Ansible compose, image pull, paid/OIDC, Terraform, starting Neo4j.
