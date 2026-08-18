# ADR 0006: Portal CI family stops at packaging

- **Status:** Accepted
- **Date:** 2026-08-17
- **Change:** `add-portal-ci-pipeline`

## Context

Release already builds an nginx image. Academy compose is a different workflow (`web-portal-cd-academy.yml`).

## Decision

CI workflows end at `dist/` zip + image tar (GHCR push off PR). They do not run Ansible. Deploy lives in the CD family ([ADR 0001](0001-portal-cd-academy-only.md)). `configure-only` may use stock nginx; `deploy` may not. That rule is CD, not CI.

## Consequences

- Fast Feedback and Integration CI do not request `packages: write`.
