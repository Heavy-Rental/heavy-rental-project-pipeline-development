# ADR 0007: Mobile Release is dispatch-only; SAST stays on Integration CI

- **Status:** Accepted
- **Date:** 2026-08-27
- **Change:** `add-mobile-ci-pipeline`
- **Amends:** [0003](0003-mobile-ci-unsigned-apk.md)

## Context

The first mobile spec subscribed Release to a published GitHub Release or a PR `develop` → `master`, and reran Security Testing and CodeQL before Packaging.

Sibling families (REST, portal, Haystack) already use `workflow_dispatch` only so the pipeline **creates** the GitHub Release. SAST and CodeQL stay on Integration CI (`develop`). Mobile should match that GitHub Flow. The unsigned APK still needs a human DAST report; ZAP/Dastardly against a container does not apply (no image).

## Decision

The Release caller is **`workflow_dispatch` only**. It must not use `on: release` or `pull_request`. Publish (`gh release create` targeting `master`) is what creates the GitHub Release.

Release jobs are Integration (always checkout `master`) → Quality Control → Packaging (`needs: [integration, quality-control]`) → DAST (MobSF static scan of the unsigned APK + `dast-combined-report-pdf`) → Publish.

Security Testing, CodeQL, and Mock Contract Tests stay on Integration CI. Release does not request `packages: write` (ADR 0003).

## Consequences

- Operators run Actions → Release → Run workflow after `master` is ready.
- Branch protection on `develop` still requires Security, CodeQL, and Mock Contract Tests.
- Unsigned APK + MobSF + GitHub Release; still no GHCR.
