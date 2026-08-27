# Web portal CI family

**Application:** Heavy-Rental/heavy-rental-react-web-portal  
**Authoring tree:** `heavy-rental-web-portal-pipeline/`  
**Stack:** React 19 + TypeScript + Vite 8 / Node 22 / npm

This family validates and packages the SPA. Academy **app CD** is [`portal-cd.md`](portal-cd.md).

Fast Feedback and Integration reusable YAML `DEFAULT_APP_REPOSITORY` is `SA62-team1/heavy-rental-react-web-portal` (local `act`). Release reusable YAML uses `Heavy-Rental/heavy-rental-react-web-portal`. When a caller runs **in** the Heavy-Rental portal repo, Fast Feedback and Integration CI check out the calling commit (into `app/`). Release always checks out **`master`**.

## GitHub Flow

```
feature branch push  →  Fast Feedback (Integration only; sole Integration-stage run for that SHA)
PR / push → develop  →  Integration CI (Integration Check reuses Fast Feedback on PR, waits if in-flight; full gates; SAST here)
workflow_dispatch     →  Release (master + QC + image + DAST + public GHCR + GitHub Release)
```

## Job graph (Integration CI)

```
assert-caller
      │
      ▼
 Integration Check    PR: reuse Fast Feedback for the head SHA (skip npm ci / install health;
                      wait if in-flight; inlined pending-run jq)
                      else: Node 22 + npm ci + lockfile / node_modules health
                      job id integration-check
      │
      ├── Quality Control        npm run lint + npx tsc -b
      ├── Security Testing       Semgrep TS/React + npm audit SARIF + Trivy
      ├── CodeQL Analysis        javascript-typescript
      └── REST Endpoint Tests    mock on 127.0.0.1:4010 (skip-clean if scripts missing)
      │
      ▼
 GitHub Flow CI Gate
```

Do **not** `uses:` `fast-feedback-pipeline.yml` from `portal-ci-caller.yml`. Copy both Integration files into the portal repo and call `./.github/workflows/integration-pipeline.yml`.

On `pull_request`, Integration Check looks up `portal-fast-feedback-caller.yml` for the head SHA (`gh run list`). A successful run skips cache / `npm ci` / install health. An in-flight run is waited on with `gh run watch`. The pending-run `jq` filter is inlined in the `PENDING_ID` / `PENDING_URL` `jq_field` calls (same quoting as `SUCCESS_ID`). Do not assign `PENDING_FILTER` and interpolate it — that construction breaks the wait.

## Job graph (Release)

SAST, CodeQL, and REST Endpoint Tests stay on Integration CI (`develop`). Release does **not** rerun them.

```
assert-caller
      │
      ▼
 Integration          Node 22 + npm ci; checkout master
      │
      ▼
 Quality Control      npm run lint + npx tsc -b
      │
      ▼
 Packaging            environment: academy; seed/scan .env.production
                      tsc -b + vite build --mode api (empty VITE_API_TARGET)
                      dist/ zip + nginx:1.27-alpine tar (no docker push)
      │
      ▼
 DAST                 ZAP + Dastardly + Nuclei against the image
      │
      ▼
 Publish              public GHCR heavy_rental_web_portal:<semver> + :latest
                      + GitHub Release on master
```

The nginx image is a React + npm + Vite static SPA (ADR 0007 / 0008). Packaging uses Environment `academy` so academy `VITE_STRIPE_PUBLISHABLE_KEY` (`pk_` only) is baked. Spring login and `/api` work after CD mounts REST ALB. No baked `REST_BASE_URL` or `http://heavy-rental-rest-api:8080`. Fast Feedback and Integration CI do not set `environment:`.

## Node / Vite tools

| Concern | Tool |
| --- | --- |
| Runtime | Node 22 |
| Install | `npm ci` when `node_modules` cache misses |
| Integration | `package-lock.json` + `node_modules` + `npm ls --depth=0`. On Integration CI pull_request, skip cache / `npm ci` / install health when Fast Feedback already succeeded for the head SHA. In-flight Fast Feedback is waited on; pending-run `jq` is inlined (`PENDING_ID` / `PENDING_URL`), not a `PENDING_FILTER` variable |
| QC | `npm run lint` (ESLint) + `npx tsc -b --pretty false` |
| REST tests | `mock:server` / `api:mock` / `start:mock` + `test:api` / `test:endpoints` / `test:rest` |
| Mock URL | `http://127.0.0.1:4010` (`MOCK_API_*`) |
| SAST | Semgrep `p/typescript` `p/react` `p/javascript` `p/nodejs` + OWASP / audit / secrets / CWE Top 25 / Gitleaks / SQL injection / JWT / insecure-transport, plus custom ERROR rules for plaintext credentials in `.env`/YAML and JS/TS assignments. Reports: `semgrep.sarif` (all severities); gate is ERROR-only |
| SCA | npm audit (high/critical fails) converted to SARIF + Trivy FS (unfixed CRITICAL fails) |
| Human security report | Combined PDF artifact `security-combined-report-pdf`; download from the PR Checks tab (workflow Summary → Artifacts, or Security Testing job summary) |
| Human DAST report | Combined PDF artifact `dast-combined-report-pdf` (`dast-reports/combined-dast-report.pdf`); download from the Release run Summary → Artifacts, the DAST job summary link, or the GitHub Release |
| Code scanning | CodeQL `javascript-typescript` |
| Package | Seed/scan `.env.production` + `tsc -b` + `vite build --mode api` (empty `VITE_API_TARGET`) → `dist/` zip + always-generated `nginx:1.27-alpine` try_files tar. Publish pushes GHCR `heavy_rental_web_portal:<semver>` + `:latest` and creates the GitHub Release. Scan for `sk_`, localhost, `heavy-rental-rest-api`. |

## Branch protection (application repo `develop`)

1. Integration Check *(highest priority)*
2. Quality Control
3. Security Testing
4. CodeQL Analysis
5. REST Endpoint Tests
6. GitHub Flow CI Gate

REST Endpoint Tests skip cleanly (job succeeds) until both a mock script and a test script exist in `package.json`. Keep the check required so it cannot be forgotten when the scripts land.

## Local validation (this repo)

```bash
actionlint heavy-rental-web-portal-pipeline/fast-feedback-ci-pipeline/fast-feedback-pipeline.yml
actionlint heavy-rental-web-portal-pipeline/fast-feedback-ci-pipeline/portal-fast-feedback-caller.yml
actionlint heavy-rental-web-portal-pipeline/integration_pipeline/integration-pipeline.yml
actionlint heavy-rental-web-portal-pipeline/integration_pipeline/portal-ci-caller.yml
actionlint heavy-rental-web-portal-pipeline/release-pipeline/release-pipeline.yml
actionlint heavy-rental-web-portal-pipeline/release-pipeline/portal-release-caller.yml
```

## Install into the application repo

```
.github/workflows/portal-fast-feedback-caller.yml
.github/workflows/fast-feedback-pipeline.yml
.github/workflows/portal-ci-caller.yml
.github/workflows/integration-pipeline.yml
.github/workflows/portal-release-caller.yml
.github/workflows/release-pipeline.yml
```

Copy destination names stay hyphenated (`integration-pipeline.yml`) even though this authoring folder is `integration_pipeline/`.

## Pipeline boundaries

| Concern | In this CI family? |
| --- | --- |
| Fast Feedback, Integration CI, Release packaging | Yes |
| Live Spring / Haystack | No |
| Academy compose | No — [`portal-cd.md`](portal-cd.md) |
| Terraform / operate | No — infra project |

## Specs

- OpenSpec: [`../../openspec/changes/add-portal-ci-pipeline/`](../../openspec/changes/add-portal-ci-pipeline/)
- OpenSPDD: [`../../spdd/analysis/add-portal-ci-pipeline.md`](../../spdd/analysis/add-portal-ci-pipeline.md)
- ADRs 0004–0008: [`../../docs/adr/`](../../docs/adr/)
