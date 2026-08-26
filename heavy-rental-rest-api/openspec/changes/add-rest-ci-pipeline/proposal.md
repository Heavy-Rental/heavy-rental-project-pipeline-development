# Proposal: Document the REST API GitHub Actions CI family (as-implemented)

## Why

`heavy-rental-rest-api/` already authors Fast Feedback, Integration CI, and Release YAML. Haystack and mobile specify that family with OpenSpec + OpenSPDD + ADRs. REST CI was “YAML headers only.” This change records the **existing** behavior so later edits have a contract. It does not add jobs or change workflows.

## What Changes

- OpenSpec capabilities for orchestration, Integration, QC, Security, CodeQL, Release packaging, and CI scope.
- OpenSPDD analysis + REASONS Canvas bound to the existing six YAML files.
- Human `specification/` index and `pipelines/rest-ci.md`.
- CI ADRs 0004–0007 (caller gate, Environment secret split, CI stops at packaging, env-driven Tomcat image).

## Capabilities

### New Capabilities

- `rest-ci-orchestration`
- `rest-ci-integration`
- `rest-ci-quality`
- `rest-ci-security`
- `rest-ci-codeql`
- `rest-ci-release`
- `rest-ci-scope`

### Modified Capabilities

- None (YAML already shipped).

## Impact

- **This repo:** specification + OpenSpec + SPDD + ADRs under `heavy-rental-rest-api/`.
- **Application repo:** no copy required for this documentation change.
- **Not in this change:** new gates, paid CD, Terraform, edits to `deploy-pipeline/` YAML.
- **As-implemented note:** Release is `workflow_dispatch` only (creates the GitHub Release). Jobs are Integration → QC → Packaging → DAST → Publish. SAST/CodeQL stay on Integration CI. Fast Feedback / Integration CI `DEFAULT_APP_REPOSITORY` is `SA62-team1/...`; Release is `Heavy-Rental/...`.
