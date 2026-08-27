# REST API CI family

**Application:** https://github.com/Heavy-Rental/heavy-rental-spring-rest-api  
**Authoring tree:** `heavy-rental-rest-api/` in this pipeline-development repo  
**Stack:** Spring Boot / Java 21 / Maven wrapper / PostgreSQL / WAR → Tomcat 10.1

This family validates and packages the service. It does not create infrastructure or operate production. Academy and paid **app CD** is [`rest-cd.md`](rest-cd.md).

Reusable YAML `DEFAULT_APP_REPOSITORY` is `SA62-team1/heavy-rental-spring-rest-api` on Fast Feedback and Integration CI (local `act` fallback). Release uses `Heavy-Rental/heavy-rental-spring-rest-api`. When a caller runs **in** the Heavy-Rental Spring repo, Fast Feedback and Integration CI check out the calling commit (into `app/`). Release always checks out **`master`**.

Callers pass `github_environment` (`integration` / `production`). Quality Control **hardcodes** `environment: integration` or `environment: production`; the input is unused.

## GitHub Flow

```
feature branch push  →  Fast Feedback (Integration only; sole Integration-stage run for that SHA)
PR / push → develop  →  Integration CI (Integration Check reuses Fast Feedback on PR; full gates; SAST here)
workflow_dispatch     →  Release (master + QC + image + DAST + public GHCR + GitHub Release)
```

## Job graph (Integration CI)

```
assert-caller
      │
      ▼
 Integration Check    PR: reuse Fast Feedback for the head SHA (skip Maven/layout)
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

## Job graph (Release)

SAST/CodeQL stay on Integration CI (`develop`). Release does **not** rerun them.

```
assert-caller
      │
      ▼
 Integration          checkout master, Java 21 + ./mvnw, layout
      │
      ▼
 Quality Control      environment: production + REST_API_DB_*
                      Docker postgres:16-alpine, compile, test, package WAR
      │
      ▼
 Packaging            versioned WAR + Tomcat image tar (needs Integration + QC)
      │
      ▼
 DAST                 run image; OWASP ZAP + Dastardly + Nuclei
      │
      ▼
 Publish              public GHCR + GitHub Release on master
```

Release QC uses Environment `production` (hardcoded) and the same `REST_API_DB_*` names as Integration (still a **local** Docker Postgres). Packaging writes a versioned WAR, a Tomcat image tar, and a localhost JDBC env file **without password**. That env file is a workflow artifact only; Academy CD does not use it. The image must accept `POSTGRES_*` / `SPRING_DATASOURCE_*` / `HAYSTACK_BASE_URL` / Stripe / `APP_JWT_SECRET` at runtime (ADR 0007); Packaging proves that with dummy env and refuses baked hostnames. **Publish** (not Packaging) pushes `ghcr.io/<owner>/heavy_rental_rest_api:<x.y.z>` and `:latest`, then creates the GitHub Release. The Release caller is `workflow_dispatch` only, so GHCR always runs on a successful dispatch.

QC “Package WAR” on Integration CI is **build verification**, not a deploy.

## Java / Spring tools

| Concern | Tool |
| --- | --- |
| JDK | Temurin 21 |
| Build | Maven wrapper (`./mvnw -B -ntp`) |
| Integration | `dependency:resolve` + `pom.xml` / `mvnw` / `src/main/java` / `src/main/resources` |
| QC tests | `./mvnw test` against `jdbc:postgresql://localhost:<PORT>/<NAME>` |
| QC package | `./mvnw -DskipTests package` (prefer `.war`) |
| SAST | Two Semgrep passes. App: `p/java` + OWASP / security-audit / secrets / CWE Top 25 / FindSecBugs / Gitleaks / SQL injection / JWT / insecure-transport, plus custom ERROR rules for plaintext credentials in Spring properties/YAML (`p/spring` is gone); excludes `.github/**`. GHA: `p/github-actions` plus custom inherit / hardcoded-secret rules (`secrets: inherit` ERROR except paid CD caller; explicit secrets-context maps allowed). Reports: `semgrep.sarif` + `semgrep-gha.sarif` (all severities); gate is ERROR-only |
| SCA / FS | Trivy FS SARIF; CRITICAL unfixed fails |
| Human security report | Combined PDF artifact `security-combined-report-pdf` (`security-reports/combined-security-report.pdf`); download from the PR Checks tab (workflow Summary → Artifacts, or Security Testing job summary) |
| Human DAST report | Combined PDF artifact `dast-combined-report-pdf` (`dast-reports/combined-dast-report.pdf`); download from the Release run Summary → Artifacts, the DAST job summary link, or the GitHub Release |
| Code scanning | CodeQL `java-kotlin` |
| Image | Always-generated `tomcat:10.1-jdk21-temurin` + `ROOT.war` + `SPRING_PROFILES_ACTIVE=prod`. WAR must include `application-prod.properties` (hyphen). No baked `POSTGRES_*` / Stripe / JWT. Packaging proves dummy `-e`, `WEB-INF`, profile env, and Tomcat TCP `:8080`. |

## Secrets

Configure on the **application** repo, not this pipeline-development repo.

| Pipeline | Where | Names |
| --- | --- | --- |
| Integration CI QC | **Repository secrets** (required for the caller map). Optionally also Environment `integration`. | `REST_API_DB_NAME`, `REST_API_DB_USER`, `REST_API_DB_PASSWORD`, `REST_API_DB_PORT` |
| Release QC + Packaging | Environment `production` (no caller map) | Same four names. Dummy local values are enough. |

`REST_API_DB_URL` is **not** a secret. QC builds `jdbc:postgresql://localhost:<PORT>/<NAME>` after Docker Postgres starts. Do not add `REST_API_CLOUD_DB_*`. Guest CD config is `heavy-rental/rest` on the instance.

Integration CI caller **does** pass `REST_API_DB_*` via an explicit `secrets:` map. A `uses:` job cannot read Environment secrets, so those values must be Repository secrets. Release caller must **not** pass a map (QC reads Environment `production`). Neither caller uses `secrets: inherit`. Do not set `environment:` on a `uses:` job.

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
```

## Install into the application repo

```
.github/workflows/rest-api-fast-feedback-caller.yml
.github/workflows/fast-feedback-pipeline.yml
.github/workflows/rest-api-ci-caller.yml
.github/workflows/integration-pipeline.yml
.github/workflows/rest-api-release-caller.yml
.github/workflows/release-pipeline.yml
```

## Pipeline boundaries

| Concern | In this CI family? |
| --- | --- |
| Fast Feedback, Integration CI, Release packaging | Yes |
| Live Academy RDS / guest compose | No — [`rest-cd.md`](rest-cd.md) |
| Terraform / create ASG | No — infra project |
| Operate (`stop` / `destroy`) | No — infra project |

## Specs

- OpenSpec: [`../../openspec/changes/add-rest-ci-pipeline/`](../../openspec/changes/add-rest-ci-pipeline/)
- OpenSPDD: [`../../spdd/analysis/add-rest-ci-pipeline.md`](../../spdd/analysis/add-rest-ci-pipeline.md)
- ADRs 0004–0007: [`../../docs/adr/`](../../docs/adr/)
