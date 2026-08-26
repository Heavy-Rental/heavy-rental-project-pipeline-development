# REASONS Canvas: add-portal-ci-pipeline

**Input analysis:** [add-portal-ci-pipeline.md](../analysis/add-portal-ci-pipeline.md)  
**Behavior contract:** [OpenSpec change](../../openspec/changes/add-portal-ci-pipeline/)

When reality diverges, fix this prompt first — then update the YAML.

---

## R — Requirements

- Three-pipeline GitHub Flow family for the React portal.
- Fast Feedback: Integration only, feature-branch pushes (ignore `master`/`develop`). No `pull_request` trigger. Sole Integration-stage run for a feature-branch SHA.
- Integration CI: PR/push `develop` + `workflow_dispatch`. Jobs: Assert caller → Integration Check → (QC ∥ Security ∥ CodeQL ∥ REST Endpoint Tests) → GitHub Flow CI Gate. On `pull_request`, Integration Check reuses a successful Fast Feedback run for the head SHA (skip cache / `npm ci` / install health). An in-flight Fast Feedback run is waited on; the pending-run jq filter is inlined in `PENDING_ID` / `PENDING_URL` (same form as `SUCCESS_ID`), not a `PENDING_FILTER` variable. The CI caller must not `uses:` `fast-feedback-pipeline.yml`.
- Release: `workflow_dispatch` only (Actions → Release → Run workflow). Jobs: Assert caller → Integration (checkout `master`) → QC → Packaging → DAST → Publish (public GHCR `heavy_rental_web_portal:<semver>` + `:latest` + GitHub Release). Do **not** use `on: release` — Publish creates the GitHub Release. SAST/CodeQL/REST tests stay on Integration CI.
- Packaging: Node 22, `npm ci`, seed/scan `.env.production`, `tsc -b` + `vite build --mode api` (not `npm run build`), empty `VITE_API_TARGET`, `dist/` zip, nginx try_files, image tar only (no `docker push`). Scan for `sk_`, localhost, `heavy-rental-rest-api`. CD mounts `/api` from SM `REST_BASE_URL`.
- Node 22 + `npm ci`. Fast Feedback / Integration CI need no GitHub Environment. Release Packaging uses Environment `academy` only to bake `vars.VITE_STRIPE_PUBLISHABLE_KEY` (`pk_`).
- Authoring path: `heavy-rental-web-portal-pipeline/integration_pipeline/`.
- This family stops at artifacts. Academy CD is `deploy-pipeline/`.

## E — Entities

Artifacts:

| Name | Source |
| --- | --- |
| Lock fingerprint | `package.json`, `package-lock.json` |
| SARIF | Semgrep, npm-audit, Trivy |
| Release zip | `dist/` contents |
| Release image tar | `heavy_rental_web_portal-image.tar.gz` |
| GHCR | `ghcr.io/<owner>/heavy_rental_web_portal:<semver>` + `:latest` (Publish after DAST) |

## A — Approach

- Keep the six CI YAML files as the implementation. Specs track Integration Check and Fast Feedback reuse.
- Fast Feedback / Integration `DEFAULT_APP_REPOSITORY`: `SA62-team1/heavy-rental-react-web-portal` (act).
- Release `DEFAULT_APP_REPOSITORY`: `Heavy-Rental/heavy-rental-react-web-portal`. Same-repo callers still check out the calling repo.

## S — Structure

```
heavy-rental-web-portal-pipeline/
  specification/
  openspec/
  spdd/
  docs/adr/
  fast-feedback-ci-pipeline/
  integration_pipeline/     # underscore
  release-pipeline/
  deploy-pipeline/
```

Job `name:` values:

- `Assert caller`
- `Integration Check` (Integration CI) / `Integration` (Fast Feedback and Release)
- `Quality Control`
- `Security Testing` (Integration CI only)
- `CodeQL Analysis` (Integration CI only)
- `REST Endpoint Tests` (Integration CI only)
- `GitHub Flow CI Gate` (Integration CI only)
- `Packaging` (Release)
- `DAST` (Release)
- `Publish` (Release)

## O — Operations

1. Document OpenSpec + OpenSPDD + ADRs (this change).
2. Do not add jobs.
3. Keep `actionlint` paths pointed at `integration_pipeline/`.

## N — Norms

- Header comments on YAML.
- `set -euo pipefail` on multi-line `run:`.
- Bind `github.*` / `inputs.*` through `env:` inside `run:`.
- SARIF is the security report standard.

## S — Safeguards (negative space)

- **DO NOT** apply Terraform or compose onto `asg-portal` in this family.
- **DO NOT** call a live Spring / Haystack URL from CI.
- **DO NOT** pass `VITE_*` REST/Haystack/API URLs or `STRIPE_API_KEY` (`sk_`) into Release `vite build`. **DO** pass academy `VITE_STRIPE_PUBLISHABLE_KEY` (`pk_` only) into that build.
- **DO NOT** bake `REST_BASE_URL` / `VITE_*` / `STRIPE_` / `AWS_` into the nginx image (`ENV`/`ARG`/`COPY .env`/`--build-arg`). A Vite `.env.production` is a **build** input only.
- **DO NOT** generate nginx `proxy_pass` to a hostname in the Release image (CD mounts `/api`).
- **DO NOT** fail REST Endpoint Tests solely because mock scripts are missing.
- **DO NOT** `docker push` from Packaging. Publish pushes after DAST.
- **DO NOT** subscribe the Release caller to `release` or `pull_request`.
- **DO NOT** `uses:` `fast-feedback-pipeline.yml` from `portal-ci-caller.yml`.
- **DO NOT** skip the Integration Check job with `if:` (reuse only skips cache / `npm ci` / install health).
- **DO NOT** assign `PENDING_FILTER` and interpolate it into `PENDING_ID` / `PENDING_URL`. Inline the pending-status jq filter (same quoting as `SUCCESS_ID`).
- **DO NOT** put `on: push` on reusable files.
- **DO NOT** use Java, Maven, uv, yarn, pnpm, or Android SDK as the portal toolchain (`npm ci` only).
- **DO NOT** cancel in-progress Release runs.
- **DO NOT** rename `integration_pipeline/` as part of this change.
