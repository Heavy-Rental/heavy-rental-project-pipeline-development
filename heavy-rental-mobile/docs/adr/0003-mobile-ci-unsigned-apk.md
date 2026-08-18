# ADR 0003: Release APK is unsigned; no GHCR

- **Status:** Accepted
- **Date:** 2026-08-17
- **Change:** `add-mobile-ci-pipeline`

## Context

Portal, REST, and Haystack Release pipelines produce a Docker image and (off PR) push GHCR for Academy CD. The mobile app is not deployed onto `asg-*`.

## Decision

Release Packaging runs `:app:assembleRelease` and uploads an unsigned APK. No keystore, Play credentials, GitHub Environment, or `packages: write`. No Docker / GHCR in v1.

## Consequences

- The artifact is not store-ready.
- Signing, AAB distribution, and any later mobile CD are a new OpenSpec change.
