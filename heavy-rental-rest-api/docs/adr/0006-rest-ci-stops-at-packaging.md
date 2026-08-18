# ADR 0006: REST CI family stops at packaging

- **Status:** Accepted
- **Date:** 2026-08-17
- **Change:** `add-rest-ci-pipeline`

## Context

Release already builds a Tomcat image. Academy compose is a different workflow (`rest-api-cd-academy.yml`). Mixing them would apply Vocareum keys on every `develop` PR.

## Decision

CI workflows end at WAR + image tar (GHCR push off PR). They do not run Ansible or SSM compose. Deploy lives in the CD family ([ADR 0001](0001-rest-cd-academy-only.md)).

## Consequences

- Integration CI “Package WAR” is build verification only.
- Fast Feedback and Integration CI do not request `packages: write`.
