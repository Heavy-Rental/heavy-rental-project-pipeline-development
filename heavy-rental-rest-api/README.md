# Heavy Rental REST API — GitHub Actions CI and app CD

Workflows and specifications for [Heavy-Rental/heavy-rental-spring-rest-api](https://github.com/Heavy-Rental/heavy-rental-spring-rest-api).

This tree (`heavy-rental-rest-api/`) authors Fast Feedback, Integration CI, Release packaging, a scheduled Security Report, and **Academy + paid app CD** (`deploy-pipeline/`). It does not provision the VPC or ASGs (infra project). Copy workflows into the Spring repo like Release.

Start here: [`specification/README.md`](specification/README.md). App-repo CD checklist: [`docs/PREPARE-SPRING-REPO.md`](docs/PREPARE-SPRING-REPO.md).

| Path | Contents |
| --- | --- |
| `specification/` | Human index and CI + CD walkthroughs |
| `openspec/` | OpenSpec behavior (requirements + scenarios) |
| `spdd/` | OpenSPDD analysis + REASONS Canvas |
| `docs/adr/` | ADRs for CI (0004–0007) and CD (0001–0003, 0008 two Actions) |
| `docs/` | App CD operate + [`PREPARE-SPRING-REPO.md`](docs/PREPARE-SPRING-REPO.md) |
| `fast-feedback-ci-pipeline/` | Integration-only feature-branch pipeline |
| `integration-pipeline/` | PR / `develop` merge gate |
| `release-pipeline/` | `workflow_dispatch` Release: checkout `master` + WAR + DAST + GHCR + GitHub Release |
| `security-report/` | Weekly/manual Code Scanning summary (not a merge gate) |
| `deploy-pipeline/` | Academy + paid app CD (discover + compose; copy into the app repo) |

## GitHub Flow

```
feature branch push  →  Fast Feedback (Integration only; sole Integration-stage run for that SHA)
PR / push → develop  →  Integration CI (Integration Check reuses Fast Feedback on PR, waits if in-flight; full gates; SAST here)
workflow_dispatch     →  Release (master + QC + image + DAST + public GHCR + GitHub Release)
```

Release does **not** rerun SAST/CodeQL. Packaging writes the WAR and image tar; **Publish** pushes public GHCR and creates the GitHub Release. The caller is `workflow_dispatch` only (it must not use `on: release` — it **creates** the GitHub Release). Academy and paid CD consume a public GHCR/ECR tag or the tar.

## Pipeline boundaries

| Concern | This family |
| --- | --- |
| Build, test, and package | In scope |
| Create or change infrastructure | Out of scope (infra project) |
| Deploy the packaged service | Academy + paid CD in `deploy-pipeline/` (copy into the app repo). Needs a public GHCR/ECR tag from Release. First-compose is infra `deploy-projects` or this CD |
| Operate the live system | Infra estate (`stop` / `destroy` / monitor). This CD can `verify` / `configure-only` / `deploy` compose. See [`docs/BOOTSTRAP.md`](docs/BOOTSTRAP.md) |

## Toolchain

**Java 21 + Maven wrapper + Spring Boot WAR + Tomcat 10.1**, not Python / Node / Android.

| Concern | Tool |
| --- | --- |
| JDK | Temurin 21 |
| Build | Maven wrapper (`./mvnw`) |
| Integration | `dependency:resolve` + layout (`pom.xml`, `mvnw`, `src/main/java`) |
| QC | compile + Spring tests against Docker `postgres:16-alpine` + package WAR |
| SAST / SCA | Semgrep Java/OWASP (app) + Semgrep GHA + Trivy |
| Code scanning | CodeQL `java-kotlin` |
| Package | versioned WAR + `tomcat:10.1-jdk21-temurin` + `ROOT.war` |

Reusable YAML `DEFAULT_APP_REPOSITORY` is `SA62-team1/heavy-rental-spring-rest-api` on Fast Feedback only (local `act` fallback). Integration CI and Release use `Heavy-Rental/heavy-rental-spring-rest-api`. When Fast Feedback or Integration CI runs **in** `Heavy-Rental/heavy-rental-spring-rest-api`, checkout is the calling commit. Release always checks out **`master`**.
