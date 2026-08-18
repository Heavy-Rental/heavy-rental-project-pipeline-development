# ADR 0004: Mock contract tests run on Integration CI only

- **Status:** Accepted
- **Date:** 2026-08-17
- **Change:** `add-mobile-ci-pipeline`

## Context

The app ships OpenAPI mock scripts (`mock:prepare`, `mock:prism`, `mock:verify`) on port 8081. That is the contract analog of portal REST endpoint tests. Release already runs a long Android SDK + Gradle path.

## Decision

Integration CI runs **Mock Contract Tests** in parallel with QC / Security / CodeQL after Integration. Release does **not** run that job. Fast Feedback is Integration only (no mocks).

## Consequences

- Branch protection on `develop` should require `Mock Contract Tests`.
- Scripts missing from `package.json` skip cleanly (same idea as portal REST tests).
