# ADR 0003: Release APK is unsigned; no GHCR

- **Status:** Accepted
- **Date:** 2026-08-17
- **Updated:** 2026-08-27
- **Change:** `add-mobile-ci-pipeline`
- **See also:** [0007](0007-mobile-ci-release-dispatch-dast.md) (dispatch-only Release, MobSF DAST, Publish)

## Context

Portal, REST, and Haystack Release pipelines produce a Docker image and (off PR) push GHCR for Academy CD. The mobile app is not deployed onto `asg-*`.

## Decision

Release Packaging runs `:app:assembleRelease` and uploads an unsigned APK. No keystore, Play credentials, GitHub Environment, or `packages: write`. No Docker / GHCR in v1. Publish attaches that APK to a GitHub Release; DAST (MobSF) scans it. Those later jobs do not add GHCR ([ADR 0007](0007-mobile-ci-release-dispatch-dast.md)).

## Consequences

- The artifact is not store-ready.
- Signing, AAB distribution, and any later mobile CD are a new OpenSpec change.
- Pipeline ADR 0003 is **not** the application ADR 003 (returnNotes echo). Mockoon policy is [ADR 0006](0006-mobile-ci-mockoon-only.md).
