# Design: Web portal GitHub Actions CI family (as-implemented)

## Context

The React portal already has reusable-caller Fast Feedback, Integration CI, and Release workflows. Academy CD is a separate family. This document describes the CI family as the YAML behaves today.

Authoring path for Integration CI is `integration_pipeline/` (underscore).

## Goals / Non-Goals

**Goals:**

- Same GitHub Flow as REST / Haystack / mobile.
- Integration Check first on Integration CI; later jobs `needs: [integration-check]`. Fast Feedback and Release keep job `integration`.
- PR Integration Check reuses a successful Fast Feedback run for the head SHA (CI caller does not `uses:` Fast Feedback). In-flight Fast Feedback is waited on with inlined pending-run jq (no `PENDING_FILTER`).
- Node 22 + npm ci + ESLint + `tsc`.
- REST endpoint tests against a local mock; skip-clean until scripts exist.
- Release artifacts consumable by Academy CD (`dist/` zip + nginx image tar; Publish pushes GHCR after DAST).

**Non-Goals:**

- Hitting live Spring / Haystack from CI
- Terraform / compose / operate
- Unifying Release `DEFAULT_APP_REPOSITORY` (`Heavy-Rental/...`) with Fast Feedback / Integration CI (`SA62-team1/...` act fallback)

## Decisions

1. **Reusable + caller gate.** Sole callers: `portal-fast-feedback-caller.yml`, `portal-ci-caller.yml`, `portal-release-caller.yml`. Integration CI caller `uses:` `./.github/workflows/integration-pipeline.yml` (copy both files into the portal repo). It does not `uses:` Fast Feedback.
2. **Node 22 + npm ci.** Integration verifies `package-lock.json` and `node_modules`, unless Integration Check reused Fast Feedback.
3. **QC is lint + typecheck.** No Postgres. Integration CI has no GitHub Environment.
4. **REST Endpoint Tests skip-clean** when `package.json` lacks both a mock script (`mock:server` / `api:mock` / `start:mock`) and a test script (`test:api` / `test:endpoints` / `test:rest`). Mock binds `127.0.0.1:4010`.
5. **Release is `workflow_dispatch` only.** Merge to `master`, then Actions → Release → Run workflow. Publish creates the GitHub Release. The caller does not subscribe to `release` or `pull_request`.
6. **Release job graph.** Assert caller → Integration (checkout `master`) → Quality Control → Packaging → DAST → Publish. SAST, CodeQL, and REST Endpoint Tests stay on Integration CI.
7. **Release Packaging** is Node 22 + `npm ci` + `tsc -b` + **`vite build --mode api`** (not `npm run build`). Job `environment: academy` so `vars.VITE_STRIPE_PUBLISHABLE_KEY` is baked (`pk_` only). Empty `VITE_API_TARGET` / other backend `VITE_*`. Scan `dist/` for `sk_` / localhost / `heavy-rental-rest-api`. Always-generate nginx try_files (no `COPY .env`). Packaging uploads the image tar and does not `docker push`.
8. **Publish** pushes `ghcr.io/<owner>/heavy_rental_web_portal:<semver>` + `:latest` after DAST, then `gh release create` on `master`.
9. **CI family stops at artifacts.** Compose and the `/api` proxy live in the CD family.
10. **`DEFAULT_APP_REPOSITORY`.** Fast Feedback and Integration use `SA62-team1/heavy-rental-react-web-portal` (local act). Release uses `Heavy-Rental/heavy-rental-react-web-portal`. Same-repo callers still check out the calling repo.
11. **Pending Fast Feedback jq.** Integration Check inlines the pending-status filter in the `PENDING_ID` / `PENDING_URL` `jq_field` calls (same quoting as `SUCCESS_ID` / `SUCCESS_URL`). It does not assign `PENDING_FILTER` and interpolate it — that construction fails the wait-for-run lookup.

## Open Questions

None. This change documents shipped YAML.
