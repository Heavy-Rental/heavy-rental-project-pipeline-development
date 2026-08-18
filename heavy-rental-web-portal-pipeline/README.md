# Heavy Rental web portal — GitHub Actions CI and Academy CD

Workflows and specifications for [Heavy-Rental/heavy-rental-react-web-portal](https://github.com/Heavy-Rental/heavy-rental-react-web-portal) (authoring-tree act fallback: `SA62-team1/heavy-rental-react-web-portal`).

This tree (`heavy-rental-web-portal-pipeline/`) authors Fast Feedback, Integration CI, Release packaging, and Academy **app CD** (`deploy-pipeline/`). It does not provision the VPC or ASGs (infra project).

Start here: [`specification/README.md`](specification/README.md). App-repo CD checklist: [`docs/PREPARE-PORTAL-REPO.md`](docs/PREPARE-PORTAL-REPO.md).

| Path | Contents |
| --- | --- |
| `specification/` | Human index and CI + CD walkthroughs |
| `openspec/` | OpenSpec behavior (requirements + scenarios) |
| `spdd/` | OpenSPDD analysis + REASONS Canvas |
| `docs/adr/` | ADRs 0001–0008 (CI 0004–0007; CD 0001–0003; 0008 spans both) |
| `docs/` | Academy CD operate ([`BOOTSTRAP.md`](docs/BOOTSTRAP.md), [`PREPARE-PORTAL-REPO.md`](docs/PREPARE-PORTAL-REPO.md), [`samples/.env.production`](docs/samples/.env.production)) |
| `fast-feedback-ci-pipeline/` | Integration-only feature-branch pipeline |
| `integration_pipeline/` | PR / `develop` merge gate (**underscore** in this tree) |
| `release-pipeline/` | `develop` → `master` / GitHub Release + `dist/` zip + Docker/GHCR |
| `deploy-pipeline/` | Academy app CD (discover + compose; copy into the app repo) |

## GitHub Flow

```
feature branch push  →  Fast Feedback (Integration only)
PR / push → develop  →  Integration CI (full gates, no packaging)
develop → master PR or published GitHub Release
                     →  Release (full gates + Vite dist zip + Docker image)
```

## Pipeline boundaries

| Concern | This family |
| --- | --- |
| Build, test, and package | In scope |
| Create or change infrastructure | Out of scope (infra project) |
| Deploy the packaged service | Academy CD in `deploy-pipeline/` |
| Operate the live system | Infra estate + this CD. See [`docs/BOOTSTRAP.md`](docs/BOOTSTRAP.md) |

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
| Package | `npm run build` → `dist/` zip + `nginx:1.27-alpine` |
