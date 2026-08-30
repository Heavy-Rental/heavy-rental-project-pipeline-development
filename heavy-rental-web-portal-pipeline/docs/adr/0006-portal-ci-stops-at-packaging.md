# ADR 0006: Portal CI family does not compose onto guests

- **Status:** Accepted
- **Date:** 2026-08-17
- **Amended:** 2026-08-26 — Release is `workflow_dispatch`; Publish pushes GHCR after DAST
- **Change:** `add-portal-ci-pipeline`

## Context

Release already builds an nginx image. Academy compose is a different workflow (`web-portal-cd-academy.yml`).

## Decision

CI workflows end at `dist/` zip + image tar + (on Release) DAST + Publish (public GHCR + GitHub Release). They do not run Ansible. Deploy lives in the CD family ([ADR 0001](0001-portal-cd-academy-only.md)). `configure-only` may use stock nginx; `deploy` may not. That rule is CD, not CI. Release is `workflow_dispatch` only; Publish creates the GitHub Release.

## Consequences

- Fast Feedback and Integration CI do not request `packages: write`.
