# Heavy Rental web portal — GitHub Actions CI and app CD

Workflows and specifications for [Heavy-Rental/heavy-rental-react-web-portal](https://github.com/Heavy-Rental/heavy-rental-react-web-portal).

This tree (`heavy-rental-web-portal-pipeline/`) authors Fast Feedback, Integration CI, Release packaging, a scheduled Security Report, and **Academy + paid app CD** (`deploy-pipeline/`). It does not provision the VPC or ASGs (infra project). Copy workflows into the React repo like Release.

Start here: [`specification/README.md`](specification/README.md). App-repo CD checklist: [`docs/PREPARE-PORTAL-REPO.md`](docs/PREPARE-PORTAL-REPO.md).

| Path | Contents |
| --- | --- |
| `specification/` | Human index and CI + CD walkthroughs |
| `openspec/` | OpenSpec behavior (requirements + scenarios) |
| `spdd/` | OpenSPDD analysis + REASONS Canvas |
| `docs/adr/` | ADRs 0001–0009 (CI 0004–0007; CD 0001–0003, 0009 two Actions; 0008 spans both) |
| `docs/` | App CD operate ([`BOOTSTRAP.md`](docs/BOOTSTRAP.md), [`PREPARE-PORTAL-REPO.md`](docs/PREPARE-PORTAL-REPO.md), [`samples/.env.production`](docs/samples/.env.production) — Release scan input, not the Vite `--mode api` file) |
| `fast-feedback-ci-pipeline/` | Integration-only feature-branch pipeline |
| `integration_pipeline/` | PR / `develop` merge gate (**underscore** in this tree) |
| `release-pipeline/` | Manual `workflow_dispatch` on `master`: QC + image + DAST + public GHCR + GitHub Release |
| `security-report/` | Weekly/manual Code Scanning summary (Monday 08:00 UTC; not a merge gate) |
| `deploy-pipeline/` | Academy + paid app CD (discover + compose; copy into the app repo) |

## GitHub Flow

```
feature branch push  →  Fast Feedback (Integration only; sole Integration-stage run for that SHA)
PR / push → develop  →  Integration CI (Integration Check reuses Fast Feedback on PR, waits if in-flight; full gates; SAST here)
workflow_dispatch     →  Release (master + QC + image + DAST + public GHCR + GitHub Release)
```

Release stops at **packaged artifacts** (`dist/` zip, image tar, public GHCR, GitHub Release). It does not deploy. Academy and paid CD in `deploy-pipeline/` consume a public GHCR/ECR tag or the tar. SAST and CodeQL stay on Integration CI. The Security Report pair is scheduled/manual only (Monday 08:00 UTC + `workflow_dispatch`); it summarizes existing Code Scanning alerts and is **not** a merge gate.

## Pipeline boundaries

| Concern | This family |
| --- | --- |
| Build, test, and package | In scope |
| Create or change infrastructure | Out of scope (infra project) |
| Deploy the packaged service | Academy and paid CD in `deploy-pipeline/`. First-compose is infra `deploy-projects` or this CD |
| Operate the live system | Infra estate (`stop` / `destroy` / monitor). This CD can `verify` / `configure-only` / `deploy` compose. See [`docs/BOOTSTRAP.md`](docs/BOOTSTRAP.md) |

## Toolchain

**Node 22 + npm + React / TypeScript / Vite**, not Java / Python / Android.

| Concern | Tool |
| --- | --- |
| Runtime | Node 22 |
| Install | `npm ci` (lockfile + `node_modules` cache) |
| QC | `npm run lint` + `npx tsc -b` |
| REST endpoint tests | Local mock on `127.0.0.1:4010` (skip-clean if scripts missing) |
| SAST / SCA | Semgrep TS/React + npm audit SARIF + Trivy |
| Code scanning | CodeQL `javascript-typescript` |
| Package | `tsc -b` + `vite build --mode api` → `dist/` zip + `nginx:1.27-alpine` tar; Publish pushes GHCR |

Checkout is the calling repository into `app/` (Fast Feedback / Integration: `github.sha`). Release always checks out **`master`**. Env `DEFAULT_APP_REPOSITORY` is set to `Heavy-Rental/heavy-rental-react-web-portal` but is **not interpolated**. `DEFAULT_APP_REF` is used only when a caller passes a different `app_repository`.
