# ADR 0004: Mock contract tests run on Integration CI only

- **Status:** Accepted
- **Date:** 2026-08-17
- **Updated:** 2026-08-27
- **Change:** `add-mobile-ci-pipeline`
- **See also:** [0006](0006-mobile-ci-mockoon-only.md) (Mockoon required; no Prism)

## Context

The app ships OpenAPI mock scripts on port 8081. That is the contract analog of portal REST endpoint tests. Release already runs a long Android SDK + Gradle path, then MobSF DAST and Publish.

## Decision

Integration CI runs **Mock Contract Tests** in parallel with QC / Security / CodeQL after Integration. Release does **not** run that job. Fast Feedback is Integration only (no mocks).

How those scripts are detected and gated is [ADR 0006](0006-mobile-ci-mockoon-only.md).

## Consequences

- Branch protection on `develop` should require `Mock Contract Tests`.
- Missing Mockoon scripts fail Integration CI (ADR 0006). They do not skip cleanly like portal REST Endpoint Tests.
