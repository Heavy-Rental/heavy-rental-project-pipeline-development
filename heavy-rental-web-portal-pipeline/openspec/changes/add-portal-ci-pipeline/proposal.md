# Proposal: Document the web portal GitHub Actions CI family (as-implemented)

## Why

`heavy-rental-web-portal-pipeline/` authors Fast Feedback, Integration CI, and Release YAML. Haystack and mobile specify that family with OpenSpec + OpenSPDD + ADRs. This change records the **as-implemented** behavior so later edits have a contract.

## What Changes

- OpenSpec capabilities for orchestration, Integration, QC, Security, CodeQL, REST endpoint tests, Release packaging, and CI scope (Integration Check, Fast Feedback reuse).
- OpenSPDD analysis + REASONS Canvas bound to the existing six YAML files.
- Human `specification/` index and `pipelines/portal-ci.md`.
- CI ADRs 0004–0008 (0007 = static SPA; 0008 = Vite `.env.production` vs AWS REST host).
- Release is `workflow_dispatch` only. Packaging seeds/scans `.env.production` then `npx tsc -b` + `npx vite build --mode api`. DAST scans the image. Publish pushes GHCR `heavy_rental_web_portal:<semver>` + `:latest` and creates the GitHub Release. Academy GitHub `VITE_*` vars other than Stripe `pk_` are not SPA config.

## Capabilities

### New Capabilities

- `portal-ci-orchestration`
- `portal-ci-integration`
- `portal-ci-quality`
- `portal-ci-security`
- `portal-ci-codeql`
- `portal-ci-rest-endpoints`
- `portal-ci-release`
- `portal-ci-scope`

### Modified Capabilities

- `portal-ci-orchestration` (Fast Feedback reuse; CI caller does not `uses:` Fast Feedback)
- `portal-ci-integration` (job id `integration-check` on Integration CI)
- `portal-ci-quality` / `portal-ci-security` / `portal-ci-codeql` / `portal-ci-rest-endpoints` (needs Integration Check)

## Impact

- **This repo:** specification + OpenSpec + SPDD + ADRs + CI YAML under `heavy-rental-web-portal-pipeline/`.
- **Not in this change:** paid CD, Terraform, edits to `deploy-pipeline/` YAML.
- **As-implemented note:** Release is `workflow_dispatch` only (creates the GitHub Release). Jobs are Integration → QC → Packaging → DAST → Publish. SAST/CodeQL/REST tests stay on Integration CI. Integration CI job is **Integration Check** (`needs: [integration-check]`) and reuses Fast Feedback on PR (inlined pending-run jq; no `PENDING_FILTER`). Fast Feedback / Integration CI `DEFAULT_APP_REPOSITORY` is `SA62-team1/...`; Release is `Heavy-Rental/...`.
