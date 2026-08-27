# ADR 0006: REST CI family stops at packaging

- **Status:** Accepted
- **Date:** 2026-08-17
- **Change:** `add-rest-ci-pipeline`

## Context

Release already builds a Tomcat image. Academy compose is a different workflow (`rest-api-cd-academy.yml`). Mixing them would apply Vocareum keys on every `develop` PR.

## Decision

CI workflows do **not** run Ansible or SSM compose. Deploy lives in the CD family ([ADR 0001](0001-rest-cd-academy-only.md)). Fast Feedback and Integration CI stop at gates (no image tar). Release continues **Packaging → DAST → Publish** (public GHCR + GitHub Release) on `workflow_dispatch` only; it does not subscribe to `on: release` or a `develop`→`master` PR.

## Consequences

- Integration CI “Package WAR” is build verification only.
- Fast Feedback and Integration CI do not request `packages: write`.
