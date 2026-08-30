# REST API CI family

**Application:** https://github.com/Heavy-Rental/heavy-rental-spring-rest-api  
**Authoring tree:** `heavy-rental-rest-api/` in this pipeline-development repo  
**Stack:** Spring Boot / Java 21 / Maven wrapper / PostgreSQL / WAR → Tomcat 10.1

This family validates and packages the service. It does not create infrastructure or operate production. Academy and paid **app CD** is [`rest-cd.md`](rest-cd.md). A scheduled Security Report pair summarizes existing Code Scanning alerts; it is not a merge gate.

Checkout is the calling repository into `app/` (Fast Feedback / Integration: `github.sha`). Release always checks out **`master`**. Env `DEFAULT_APP_REPOSITORY` is set (`SA62-team1/heavy-rental-spring-rest-api` on Fast Feedback, `Heavy-Rental/heavy-rental-spring-rest-api` on Integration CI and Release) but is **not interpolated**. `DEFAULT_APP_REF` is used only when a caller passes a different `app_repository`.

Callers pass `github_environment` (`integration` / `production`). Quality Control **hardcodes** `environment: integration` or `environment: production`; the input is unused.

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
 Integration Check    PR: reuse Fast Feedback for the head SHA (skip Maven/layout;
                      wait if in-flight)
                      else: Java 21 + ./mvnw dependency:resolve + layout
                      job id integration-check (not environment: integration)
      │
      ├── Quality Control     environment: integration + REST_API_DB_* (caller map)
      │                       Docker postgres:16-alpine, compile, test, package WAR
      ├── Security Testing    Semgrep app + GHA + Trivy SARIF
      └── CodeQL Analysis     java-kotlin / security-and-quality
      │
      ▼
 GitHub Flow CI Gate
```

Do **not** `uses:` `fast-feedback-pipeline.yml` from `rest-api-ci-caller.yml`. Copy both Integration files into the Spring repo and call `./.github/workflows/integration-pipeline.yml`.

On `pull_request`, Integration Check looks up `rest-api-fast-feedback-caller.yml` for the head SHA (`gh run list`). A successful run skips Maven/layout. An in-flight run is waited on with `gh run watch`. Push to `develop` and `workflow_dispatch` always run Maven/layout locally.

## Job graph (Release)

SAST/CodeQL stay on Integration CI (`develop`). Release does **not** rerun them.

```
assert-caller
      │
      ▼
 Integration          checkout master, Java 21 + ./mvnw, layout
      │
      ▼
 Quality Control      environment: production + REST_API_DB_* (caller map)
                      Docker postgres:16-alpine, compile, test, package WAR
      │
      ▼
 Packaging            versioned WAR + Tomcat image tar (needs Integration + QC)
      │
      ▼
 DAST                 run image; wait `GET :8080/actuator/health`; OWASP ZAP (gate) + Dastardly (gate) + Nuclei (report-only)
      │
      ▼
 Publish              public GHCR + GitHub Release on master
```

Release QC uses Environment `production` (hardcoded) and the same `REST_API_DB_*` names as Integration (still a **local** Docker Postgres). The Release caller forwards those names via an explicit `secrets:` map from **Repository** secrets (same pattern as Integration). Packaging writes a versioned WAR, a Tomcat image tar, and a localhost JDBC env file **without password**. That env file is a workflow artifact only; Academy CD does not use it. The image must accept `POSTGRES_*` / `SPRING_DATASOURCE_*` / `HAYSTACK_BASE_URL` / Stripe / `APP_JWT_SECRET` at runtime (ADR 0007); Packaging proves that with dummy env and refuses baked hostnames. **Publish** (not Packaging) pushes `ghcr.io/<owner>/heavy_rental_rest_api:<x.y.z>` and `:latest`, then creates the GitHub Release. The Release caller is `workflow_dispatch` only (required input `run_name` sets the Actions-list title), so GHCR always runs on a successful dispatch. Publish warns if the GHCR package is not public; it does not flip visibility.

QC “Package WAR” on Integration CI is **build verification**, not a deploy.

## Java / Spring tools

| Concern | Tool |
| --- | --- |
| JDK | Temurin 21 |
| Build | Maven wrapper (`./mvnw -B -ntp`) |
| Integration | `dependency:resolve` + `pom.xml` / `mvnw` / `src/main/java` / `src/main/resources`. On Integration CI pull_request, skip Maven/layout when Fast Feedback already succeeded for the head SHA. In-flight Fast Feedback is waited on (`gh run watch`) |
| QC tests | `./mvnw test` against `jdbc:postgresql://localhost:<PORT>/<NAME>` |
| QC package | `./mvnw -DskipTests package` (prefer `.war`) |
| SAST | Two Semgrep passes. App: `p/java` + OWASP / security-audit / secrets / CWE Top 25 / FindSecBugs / Gitleaks / SQL injection / JWT / insecure-transport, plus custom ERROR rules for plaintext credentials in Spring properties/YAML (`p/spring` is gone); excludes `.github/**`. GHA: `p/github-actions` plus custom inherit / hardcoded-secret rules (`secrets: inherit` ERROR except paid CD caller; explicit secrets-context maps allowed). Reports: `semgrep.sarif` + `semgrep-gha.sarif` (all severities); gate is ERROR-only |
| SCA / FS | Trivy FS SARIF; CRITICAL unfixed fails |
| Human security report | Combined PDF artifact `security-combined-report-pdf` (`security-reports/combined-security-report.pdf`); download from the PR Checks tab (workflow Summary → Artifacts, or Security Testing job summary) |
| Human DAST report | Combined PDF artifact `dast-combined-report-pdf` (`dast-reports/combined-dast-report.pdf`); download from the Release run Summary → Artifacts, the DAST job summary link, or the GitHub Release |
| Code scanning | CodeQL `java-kotlin` |
| Image | Always-generated `tomcat:10.1-jdk21-temurin` + `ROOT.war` + `SPRING_PROFILES_ACTIVE=prod`. WAR must include `application-prod.properties` (hyphen). No baked `POSTGRES_*` / Stripe / JWT. Packaging proves dummy `-e`, `WEB-INF`, profile env, and Tomcat TCP `:8080`. Tar artifact: `heavy_rental_rest_api-image.tar.gz`. Publish pushes `ghcr.io/<owner>/heavy_rental_rest_api:<x.y.z>` + `:latest`. |

## Secrets

Configure on the **application** repo, not this pipeline-development repo.

| Pipeline | Where | Names |
| --- | --- | --- |
| Integration CI QC | **Repository secrets** (required for the caller map). Optionally also Environment `integration`. | `REST_API_DB_NAME`, `REST_API_DB_USER`, `REST_API_DB_PASSWORD`, `REST_API_DB_PORT` |
| Release QC + Packaging | **Repository secrets** (required for the caller map). Optionally also Environment `production`. | Same four names. Dummy local values are enough. |

`REST_API_DB_URL` is **not** a secret. QC builds `jdbc:postgresql://localhost:<PORT>/<NAME>` after Docker Postgres starts. Do not add `REST_API_CLOUD_DB_*`. Guest CD config is `heavy-rental/rest` on the instance.

Both Integration CI and Release callers pass `REST_API_DB_*` via an explicit `secrets:` map. A `uses:` job cannot read Environment secrets, so those values must be Repository secrets. QC jobs still use `environment: integration` / `environment: production`. Neither caller uses `secrets: inherit`. Do not set `environment:` on a `uses:` job.

## Branch protection (application repo `develop`)

1. Integration Check *(highest priority)*
2. Quality Control
3. Security Testing
4. CodeQL Analysis
5. GitHub Flow CI Gate

## Local validation (this repo)

```bash
actionlint heavy-rental-rest-api/fast-feedback-ci-pipeline/fast-feedback-pipeline.yml
actionlint heavy-rental-rest-api/fast-feedback-ci-pipeline/rest-api-fast-feedback-caller.yml
actionlint heavy-rental-rest-api/integration-pipeline/integration-pipeline.yml
actionlint heavy-rental-rest-api/integration-pipeline/rest-api-ci-caller.yml
actionlint heavy-rental-rest-api/release-pipeline/release-pipeline.yml
actionlint heavy-rental-rest-api/release-pipeline/rest-api-release-caller.yml
actionlint heavy-rental-rest-api/security-report/security-report-pipeline.yml
actionlint heavy-rental-rest-api/security-report/rest-api-security-report-caller.yml
```

## Install into the application repo

```
.github/workflows/rest-api-fast-feedback-caller.yml
.github/workflows/fast-feedback-pipeline.yml
.github/workflows/rest-api-ci-caller.yml
.github/workflows/integration-pipeline.yml
.github/workflows/rest-api-release-caller.yml
.github/workflows/release-pipeline.yml
.github/workflows/rest-api-security-report-caller.yml
.github/workflows/security-report-pipeline.yml
```

The Security Report pair is a **scheduled/manual summary** of existing Code Scanning alerts (Monday 06:00 UTC + `workflow_dispatch`). It does not scan, is not a `develop` branch-protection check, and does not run on push or pull_request.

## Pipeline boundaries

| Concern | In this CI family? |
| --- | --- |
| Fast Feedback, Integration CI, Release packaging | Yes |
| Security Report (summarize existing Code Scanning alerts) | Yes — reporting only; not a merge gate |
| Live Academy RDS / guest compose | No — [`rest-cd.md`](rest-cd.md) |
| Terraform / create ASG | No — infra project |
| Operate (`stop` / `destroy`) | No — infra project |

## Specs

- OpenSpec: [`../../openspec/changes/add-rest-ci-pipeline/`](../../openspec/changes/add-rest-ci-pipeline/)
- OpenSPDD: [`../../spdd/analysis/add-rest-ci-pipeline.md`](../../spdd/analysis/add-rest-ci-pipeline.md)
- ADRs 0004–0007: [`../../docs/adr/`](../../docs/adr/)
