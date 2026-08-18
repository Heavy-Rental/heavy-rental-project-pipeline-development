# ADR 0005: Haystack CI uses reusable workflows plus a sole-allowed caller

- **Status:** Accepted
- **Date:** 2026-08-17
- **Change:** `add-haystack-ci-pipeline`

## Context

REST, portal, and mobile already ship as `workflow_call` files that reject any caller other than their matching `*-caller.yml`. Haystack needs the same install story: copy six YAML files into the app repo.

## Decision

Each reusable file exposes only `on: workflow_call`. `assert-caller` fails unless `github.workflow_ref` ends with the matching caller filename. Fast Feedback, Integration CI, and Release are three pairs, not one mega-workflow.

## Consequences

- Operators install caller + reusable side by side under `.github/workflows/`.
- A reusable file with `push` / `pull_request` / `workflow_dispatch` of its own is out of spec.
- Local `act` must skip the filename gate (`ACT=true`); GitHub-hosted runners never set that.
