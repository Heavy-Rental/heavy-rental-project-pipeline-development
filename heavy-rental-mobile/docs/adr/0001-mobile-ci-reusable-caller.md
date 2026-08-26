# ADR 0001: Mobile CI uses reusable workflows plus a sole-allowed caller

- **Status:** Accepted
- **Date:** 2026-08-17
- **Updated:** 2026-08-26
- **Change:** `add-mobile-ci-pipeline`

## Context

REST and portal already ship as `workflow_call` files that reject any caller other than their matching `*-caller.yml`. Mobile needs the same install story.

## Decision

Each reusable file exposes only `on: workflow_call`. `assert-caller` fails unless `github.workflow_ref` ends with the matching caller filename. Fast Feedback, Integration CI, and Release are three pairs.

## Consequences

- Operators copy six YAML files into `Heavy-Rental/heavy-rental-mobile` `.github/workflows/`.
- Local `act` skips the filename gate when `ACT=true`.
- Integration CI caller must not `uses:` `fast-feedback-pipeline.yml`. On pull_request, Integration reuses a successful Fast Feedback run for the PR head SHA. An in-flight run is waited on. The pending-run jq filter is inlined in `PENDING_ID` / `PENDING_URL` (same form as `SUCCESS_ID`); splitting it into a `PENDING_FILTER` variable breaks the lookup.
