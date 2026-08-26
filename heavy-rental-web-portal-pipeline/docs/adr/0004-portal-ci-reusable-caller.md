# ADR 0004: Portal CI uses reusable workflows plus a sole-allowed caller

- **Status:** Accepted
- **Date:** 2026-08-17
- **Updated:** 2026-08-26
- **Change:** `add-portal-ci-pipeline`

## Context

REST, Haystack, and mobile CI install as caller + reusable pairs. Portal already follows that shape.

## Decision

Each reusable file exposes only `on: workflow_call`. `assert-caller` fails unless `github.workflow_ref` ends with the matching caller (`portal-fast-feedback-caller.yml`, `portal-ci-caller.yml`, `portal-release-caller.yml`).

## Consequences

- Operators copy six YAML files into the React repo `.github/workflows/`. Callers `uses:` the sibling reusable (`./.github/workflows/integration-pipeline.yml` and peers).
- The authoring folder `integration_pipeline/` does not change the install filename `integration-pipeline.yml`.
- Integration CI caller must not `uses:` `fast-feedback-pipeline.yml`. On pull_request, Integration Check reuses a successful Fast Feedback run for the PR head SHA.
