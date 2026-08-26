# ADR 0004: REST CI uses reusable workflows plus a sole-allowed caller

- **Status:** Accepted
- **Date:** 2026-08-17
- **Updated:** 2026-08-26
- **Change:** `add-rest-ci-pipeline`

## Context

Haystack, portal, and mobile CI install as caller + reusable pairs. REST already follows that shape; this records the decision.

## Decision

Each reusable file exposes only `on: workflow_call`. `assert-caller` fails unless `github.workflow_ref` ends with the matching caller (`rest-api-fast-feedback-caller.yml`, `rest-api-ci-caller.yml`, `rest-api-release-caller.yml`).

## Consequences

- Operators copy six YAML files into the Spring repo `.github/workflows/`. Callers `uses:` the sibling reusable (`./.github/workflows/integration-pipeline.yml` and peers).
- Integration CI caller passes `REST_API_DB_*` via an explicit `secrets:` map from Repository secrets. Release caller does not pass a map (QC reads Environment `production`). Neither uses `secrets: inherit`. `environment:` on a `uses:` job is invalid.
- Integration CI caller must not `uses:` `fast-feedback-pipeline.yml`. On pull_request, Integration Check reuses a successful Fast Feedback run for the PR head SHA.
