# Proposal: Add mobile GitHub Actions CI family

## Why

[Heavy-Rental/heavy-rental-mobile](https://github.com/Heavy-Rental/heavy-rental-mobile) has no GitHub Actions workflows. The REST API and web portal already share a reusable-caller GitHub Flow family (fast feedback, integration CI, release). The Android app needs the same gates so feature branches, PRs into `develop`, and `workflow_dispatch` Release from `master` are validated consistently.

## What Changes

- Add three reusable workflows plus three sole-allowed callers, authored in this pipeline-development repo under `heavy-rental-mobile/`.
- Integration CI is the merge gate: Integration first, then Quality Control, Security Testing, CodeQL, and Mock Contract Tests in parallel, then an aggregate GitHub Flow CI Gate.
- Fast feedback runs Integration only on feature-branch pushes.
- Release is `workflow_dispatch` only (creates the GitHub Release). Jobs: Integration (checkout `master`) → QC → Packaging (unsigned APK) → DAST (MobSF) → Publish. No Play signing, no GHCR. SAST, CodeQL, and Mock Contract Tests stay on Integration CI.
- Specify the pipelines with OpenSpec (behavior) and OpenSPDD (REASONS Canvas implementation contract).

## Capabilities

### New Capabilities

- `mobile-ci-orchestration`: callers, triggers, concurrency, caller gate, checkout modes
- `mobile-ci-integration`: JDK 17, Android SDK, Gradle wrapper, layout checks
- `mobile-ci-quality`: lint, JVM unit tests, assembleDebug
- `mobile-ci-security`: Semgrep + Trivy + SARIF + combined PDF
- `mobile-ci-codeql`: CodeQL java-kotlin
- `mobile-ci-mocks`: OpenAPI Mockoon (`mock:mockoon`) + `mock:verify` (required; no Prism)
- `mobile-ci-release`: unsigned versioned APK, MobSF DAST, GitHub Release (no GHCR)

### Modified Capabilities

- `mobile-ci-orchestration` (Release is `workflow_dispatch` only; Packaging / DAST / Publish; `checks: write` on Integration CI)
- `mobile-ci-mocks` (Mockoon-only; fail if scripts missing; `MOCK_EXPECT_ECHO=1`)
- `mobile-ci-release` (DAST + Publish; SAST/CodeQL not on Release)
- `mobile-ci-security` (SARIF + combined PDF as implemented; no required `semgrep.json` / `semgrep.txt` files)

## Impact

- **Application repo:** operators copy the six YAML files into `Heavy-Rental/heavy-rental-mobile` `.github/workflows/`.
- **This repo:** new `heavy-rental-mobile/` tree (specs + workflows). No change to REST API or portal pipelines.
- **Not in this change:** emulator tests, Play signing, GHCR, `overall-project-deploy-pipeline` wiring, or edits to the Android product specs.
- **As-implemented note:** Mock Contract Tests require `mock:mockoon` and `mock:verify` (application ADR 003 returnNotes echo is Mockoon-only; pipeline [ADR 0006](../../../docs/adr/0006-mobile-ci-mockoon-only.md)). Release is `workflow_dispatch` only ([ADR 0007](../../../docs/adr/0007-mobile-ci-release-dispatch-dast.md)). Jobs are Integration → QC → Packaging → DAST → Publish.
