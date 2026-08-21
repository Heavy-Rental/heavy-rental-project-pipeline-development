# Web portal CI family

**Application:** Heavy-Rental/heavy-rental-react-web-portal (YAML `DEFAULT_APP_REPOSITORY`: `SA62-team1/heavy-rental-react-web-portal` for local act)  
**Authoring tree:** `heavy-rental-web-portal-pipeline/`  
**Stack:** React 19 + TypeScript + Vite 8 / Node 22 / npm

This family validates and packages the SPA. Academy **app CD** is [`portal-cd.md`](portal-cd.md).

When the caller runs **in** the portal repo, checkout is the calling repo (into `app/`).

## GitHub Flow

```
feature branch push  →  Fast Feedback (Integration only)
PR / push → develop  →  Integration CI (full gates, no packaging)
develop → master PR or published GitHub Release
                     →  Release (full gates + dist zip + Docker)
```

## Job graph (Integration CI)

```
assert-caller
      │
      ▼
 Integration          Node 22 + npm ci + lockfile / node_modules health
      │
      ├── Quality Control        npm run lint + npx tsc -b
      ├── Security Testing       Semgrep TS/React + npm audit SARIF + Trivy
      ├── CodeQL Analysis        javascript-typescript
      └── REST Endpoint Tests    mock on 127.0.0.1:4010 (skip-clean if scripts missing)
      │
      ▼
 GitHub Flow CI Gate
```

Release adds **Packaging** after Integration + QC + Security + CodeQL. Release does **not** run REST Endpoint Tests. The nginx image is a React + npm + Vite static SPA (ADR 0007 / 0008): Packaging uses Environment `academy`, seeds/scans `.env.production`, then `tsc -b` + **`vite build --mode api`** with empty `VITE_API_TARGET` / backend `VITE_*` and academy `VITE_STRIPE_PUBLISHABLE_KEY` (`pk_` only). Spring login and `/api` work after CD mounts REST ALB. No baked `REST_BASE_URL` or `http://heavy-rental-rest-api:8080`.

No GitHub Environment or repository secrets are required for v1 CI.

## Node / Vite tools

| Concern | Tool |
| --- | --- |
| Runtime | Node 22 |
| Install | `npm ci` when `node_modules` cache misses |
| Integration | `package-lock.json` + `node_modules` + `npm ls --depth=0` |
| QC | `npm run lint` (ESLint) + `npx tsc -b --pretty false` |
| REST tests | `mock:server` / `api:mock` / `start:mock` + `test:api` / `test:endpoints` / `test:rest` |
| Mock URL | `http://127.0.0.1:4010` (`MOCK_API_*`) |
| SAST | Semgrep `p/typescript` `p/react` `p/javascript` `p/nodejs` + OWASP / audit / secrets / CWE Top 25 / Gitleaks / SQL injection / JWT / insecure-transport, plus custom ERROR rules for plaintext credentials in `.env`/YAML and JS/TS assignments |
| SCA | npm audit converted to SARIF + Trivy FS |
| Code scanning | CodeQL `javascript-typescript` |
| Package | Seed/scan `.env.production` + `tsc -b` + `vite build --mode api` (empty `VITE_API_TARGET`) → `dist/` zip + always-generated `nginx:1.27-alpine` try_files. GHCR `heavy_rental_web_portal:<semver>` + `:latest` off PR. Scan for `sk_`, localhost, `heavy-rental-rest-api`. |

## Branch protection (application repo `develop`)

1. Integration *(highest priority)*
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
- ADRs 0004–0006: [`../../docs/adr/`](../../docs/adr/)
