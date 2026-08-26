# Proposal: Document the web portal GitHub Actions CI family (as-implemented)

## Why

`heavy-rental-web-portal-pipeline/` authors Fast Feedback, Integration CI, and Release YAML. Haystack and mobile specify that family with OpenSpec + OpenSPDD + ADRs. This change records the **existing** behavior. It does not add jobs or change workflows.

## What Changes

- OpenSpec capabilities for orchestration, Integration, QC, Security, CodeQL, REST endpoint tests, Release packaging, and CI scope.
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

- None (YAML already shipped).

## Impact

- **This repo:** specification + OpenSpec + SPDD + ADRs under `heavy-rental-web-portal-pipeline/`.
- **Not in this change:** new gates, paid CD, Terraform, edits to `deploy-pipeline/` YAML.
