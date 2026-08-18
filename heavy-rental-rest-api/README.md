# Heavy Rental REST API — GitHub Actions CI and Academy CD

Workflows and specifications for [Heavy-Rental/heavy-rental-spring-rest-api](https://github.com/Heavy-Rental/heavy-rental-spring-rest-api).

This tree (`heavy-rental-rest-api/`) authors Fast Feedback, Integration CI, Release packaging, and Academy **app CD** (`deploy-pipeline/`). It does not provision the VPC or ASGs (infra project). Copy workflows into the Spring repo like Release.

Start here: [`specification/README.md`](specification/README.md). App-repo CD checklist: [`docs/PREPARE-SPRING-REPO.md`](docs/PREPARE-SPRING-REPO.md).

| Path | Contents |
| --- | --- |
| `specification/` | Human index and CI + CD walkthroughs |
| `openspec/` | OpenSpec behavior (requirements + scenarios) |
| `spdd/` | OpenSPDD analysis + REASONS Canvas |
| `docs/adr/` | ADRs for CI (0004–0007) and CD (0001–0003) |
| `docs/` | Academy CD operate + [`PREPARE-SPRING-REPO.md`](docs/PREPARE-SPRING-REPO.md) |
| `fast-feedback-ci-pipeline/` | Integration-only feature-branch pipeline |
| `integration-pipeline/` | PR / `develop` merge gate |
| `release-pipeline/` | `develop` → `master` / GitHub Release + WAR + Docker/GHCR |
| `deploy-pipeline/` | Academy app CD (discover + compose; copy into the app repo) |

## GitHub Flow

```
feature branch push  →  Fast Feedback (Integration only)
PR / push → develop  →  Integration CI (full gates, no packaging)
develop → master PR or published GitHub Release
                     →  Release (full gates + WAR + Docker image)
```

Release stops at **packaged artifacts** (WAR, image tar; GHCR push off pull request). Academy CD consumes a public GHCR/ECR tag or the tar.

## Pipeline boundaries

| Concern | This family |
| --- | --- |
| Build, test, and package | In scope |
| Create or change infrastructure | Out of scope (infra project) |
| Deploy the packaged service | Academy CD in `deploy-pipeline/` (copy into the app repo). Needs a public GHCR/ECR tag from Release |
| Operate the live system | Infra estate + this CD. See [`docs/BOOTSTRAP.md`](docs/BOOTSTRAP.md) |

## Toolchain

**Java 21 + Maven wrapper + Spring Boot WAR + Tomcat 10.1**, not Python / Node / Android.

| Concern | Tool |
| --- | --- |
| JDK | Temurin 21 |
| Build | Maven wrapper (`./mvnw`) |
| Integration | `dependency:resolve` + layout (`pom.xml`, `mvnw`, `src/main/java`) |
| QC | compile + Spring tests against Docker `postgres:16-alpine` + package WAR |
| SAST / SCA | Semgrep Java/OWASP + Trivy |
| Code scanning | CodeQL `java-kotlin` |
| Package | versioned WAR + `tomcat:10.1-jdk21-temurin` + `ROOT.war` |

Reusable YAML `DEFAULT_APP_REPOSITORY` is `SA62-team1/heavy-rental-spring-rest-api` (local `act` fallback). When Release/CI runs **in** `Heavy-Rental/heavy-rental-spring-rest-api`, checkout is the calling repo.
