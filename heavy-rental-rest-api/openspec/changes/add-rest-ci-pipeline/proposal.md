# Proposal: Document the REST API GitHub Actions CI family (as-implemented)

## Why

`heavy-rental-rest-api/` already authors Fast Feedback, Integration CI, and Release YAML. Haystack and mobile specify that family with OpenSpec + OpenSPDD + ADRs. This change records the **as-implemented** behavior so later edits have a contract.

## What Changes

- OpenSpec capabilities for orchestration, Integration, QC, Security, CodeQL, Release packaging, and CI scope (Integration Check, Fast Feedback reuse, Integration explicit secrets map, split Semgrep).
- OpenSPDD analysis + REASONS Canvas bound to the existing six YAML files.
- Human `specification/` index and `pipelines/rest-ci.md`.
- CI ADRs 0004–0007 (caller gate, Integration repo-secret map vs Release Environment, CI stops at packaging, env-driven Tomcat image).

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

- `rest-ci-orchestration` (Fast Feedback reuse; Integration caller explicit secrets map)
- `rest-ci-integration` (job id `integration-check` on Integration CI)
- `rest-ci-quality` / `rest-ci-security` / `rest-ci-codeql` / `rest-ci-scope` (needs Integration Check; split Semgrep; repo vs Environment secrets)

## Impact

- **This repo:** specification + OpenSpec + SPDD + ADRs under `heavy-rental-rest-api/`.
- **Application repo:** copy the six CI YAML files; configure Integration `REST_API_DB_*` as Repository secrets.
- **Not in this change:** paid CD, Terraform.
- **As-implemented note:** Release is `workflow_dispatch` only (creates the GitHub Release). Jobs are Integration → QC → Packaging → DAST → Publish. SAST/CodeQL stay on Integration CI. Integration CI job is **Integration Check** (`needs: [integration-check]`) and reuses Fast Feedback on PR. Integration caller passes an explicit `REST_API_DB_*` map; Release caller does not. Fast Feedback `DEFAULT_APP_REPOSITORY` is `SA62-team1/...` (act); Integration CI and Release are `Heavy-Rental/...`. A scheduled Security Report pair summarizes existing Code Scanning alerts (not a merge gate).
