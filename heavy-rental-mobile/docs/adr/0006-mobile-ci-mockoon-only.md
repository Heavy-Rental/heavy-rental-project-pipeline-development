# ADR 0006: Mock Contract Tests are Mockoon-only and required

- **Status:** Accepted
- **Date:** 2026-08-27
- **Change:** `add-mobile-ci-pipeline`
- **Amends:** [0004](0004-mobile-ci-mocks-on-integration.md)

## Context

The first mobile OpenSpec treated Mock Contract Tests like portal REST Endpoint Tests: prefer `mock:prism`, fall back to `mock:mockoon`, and skip cleanly when scripts were missing.

The Android application ADR 003 (returnNotes echo) is **Mockoon-only**. Prism does not implement that echo, so a Prism fallback would pass CI against a mock that is not the contract the app tests. Pipeline ADR 0003 is a different decision (unsigned APK, no GHCR) and must not be confused with the application ADR.

## Decision

Mock Contract Tests require `package.json` scripts `mock:mockoon` and `mock:verify`. Missing either script **fails** the job. CI SHALL NOT select `mock:prism` and SHALL NOT skip cleanly.

Verify runs with `MOCK_EXPECT_ECHO=1`. `mock:prepare` is optional. Listen address remains `127.0.0.1:8081`.

YAML comments that say “ADR 003 returnNotes echo” mean the **application** ADR, not pipeline ADR 0003.

## Consequences

- Operators must keep `mock:mockoon` and `mock:verify` in the mobile `package.json`.
- Portal skip-clean (ADR 0005 there) is not copied here.
- OpenSpec `mobile-ci-mocks` and the OpenSPDD canvas record this as fail-closed behavior.
