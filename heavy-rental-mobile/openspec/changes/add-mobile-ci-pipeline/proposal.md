# Proposal: Add mobile GitHub Actions CI family

## Why

[Heavy-Rental/heavy-rental-mobile](https://github.com/Heavy-Rental/heavy-rental-mobile) has no GitHub Actions workflows. The REST API and web portal already share a reusable-caller GitHub Flow family (fast feedback, integration CI, release). The Android app needs the same gates so feature branches, PRs into `develop`, and `develop` → `master` / published releases are validated consistently.

## What Changes

- Add three reusable workflows plus three sole-allowed callers, authored in this pipeline-development repo under `heavy-rental-mobile/`.
- Integration CI is the merge gate: Integration first, then Quality Control, Security Testing, CodeQL, and Mock Contract Tests in parallel, then an aggregate GitHub Flow CI Gate.
- Fast feedback runs Integration only on feature-branch pushes.
- Release runs the same gates plus unsigned APK packaging (no Play signing, no GHCR in this change).
- Specify the pipelines with OpenSpec (behavior) and OpenSPDD (REASONS Canvas implementation contract).

## Capabilities

### New Capabilities

- `mobile-ci-orchestration`: callers, triggers, concurrency, caller gate, checkout modes
- `mobile-ci-integration`: JDK 17, Android SDK, Gradle wrapper, layout checks
- `mobile-ci-quality`: lint, JVM unit tests, assembleDebug
- `mobile-ci-security`: Semgrep + Trivy + SARIF
- `mobile-ci-codeql`: CodeQL java-kotlin
- `mobile-ci-mocks`: OpenAPI mock prepare / Prism / verify
- `mobile-ci-release`: unsigned versioned APK artifacts

### Modified Capabilities

- None (greenfield for this repo’s mobile pipelines).

## Impact

- **Application repo:** operators copy the six YAML files into `Heavy-Rental/heavy-rental-mobile` `.github/workflows/`.
- **This repo:** new `heavy-rental-mobile/` tree (specs + workflows). No change to REST API or portal pipelines.
- **Not in this change:** emulator tests, Play signing, GHCR, `overall-project-deploy-pipeline` wiring, or edits to the Android product specs.
