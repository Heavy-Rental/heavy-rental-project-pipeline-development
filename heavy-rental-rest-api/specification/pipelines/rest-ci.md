# REST API CI family

**Application:** https://github.com/Heavy-Rental/heavy-rental-spring-rest-api  
**Authoring tree:** `heavy-rental-rest-api/` in this pipeline-development repo  
**Stack:** Spring Boot / Java 21 / Maven wrapper / PostgreSQL / WAR → Tomcat 10.1

This family validates and packages the service. It does not create infrastructure or operate production. Academy **app CD** is [`rest-cd.md`](rest-cd.md).

Reusable YAML `DEFAULT_APP_REPOSITORY` is `SA62-team1/heavy-rental-spring-rest-api` (local `act`). When the caller runs **in** the Heavy-Rental Spring repo, checkout is the calling repo (into `app/`).

## GitHub Flow

```
feature branch push  →  Fast Feedback (Integration only)
PR / push → develop  →  Integration CI (full gates, no packaging)
develop → master PR or published GitHub Release
                     →  Release (full gates + WAR + Docker)
```

## Job graph (Integration CI)

```
assert-caller
      │
      ▼
 Integration          Java 21 + ./mvnw dependency:resolve + layout
      │
      ├── Quality Control     environment: integration + REST_API_DB_*
      │                       Docker postgres:16-alpine, compile, test, package WAR
      ├── Security Testing    Semgrep Java/OWASP + Trivy SARIF
      └── CodeQL Analysis     java / security-and-quality
      │
      ▼
 GitHub Flow CI Gate
```

Release adds **Packaging** after Integration + QC + Security + CodeQL. Release QC uses Environment `production` and `REST_API_CLOUD_DB_*` (still a **local** Docker Postgres for tests). Packaging writes a versioned WAR, a Tomcat image tar, GHCR push off PR, and a cloud JDBC env file **without password**. That env file is a workflow artifact only. The image must accept `POSTGRES_*` / `SPRING_DATASOURCE_*` / `HAYSTACK_BASE_URL` / Stripe / `APP_JWT_SECRET` at runtime (ADR 0007); Packaging proves that with dummy env and refuses baked hostnames.

QC “Package WAR” on Integration CI is **build verification**, not a deploy.

## Java / Spring tools

| Concern | Tool |
| --- | --- |
| JDK | Temurin 21 |
| Build | Maven wrapper (`./mvnw -B -ntp`) |
| Integration | `dependency:resolve` + `pom.xml` / `mvnw` / `src/main/java` / `src/main/resources` |
| QC tests | `./mvnw test` against `jdbc:postgresql://localhost:<PORT>/<NAME>` |
| QC package | `./mvnw -DskipTests package` (prefer `.war`) |
| SAST | Semgrep `p/java` + OWASP / security-audit / secrets (`p/spring` is gone) |
| SCA / FS | Trivy FS SARIF; CRITICAL unfixed fails |
| Code scanning | CodeQL `java-kotlin` |
| Image | Always-generated `tomcat:10.1-jdk21-temurin` + `ROOT.war` + `SPRING_PROFILES_ACTIVE=prod`. WAR must include `application-prod.properties` (hyphen). No baked `POSTGRES_*` / Stripe / JWT. Packaging proves dummy `-e`, `WEB-INF`, profile env, and Tomcat TCP `:8080`. |

## Secrets

Configure on the **application** repo, not this pipeline-development repo.

| Pipeline | Environment | Names |
| --- | --- | --- |
| Integration CI QC | `integration` | `REST_API_DB_NAME`, `REST_API_DB_USER`, `REST_API_DB_PASSWORD`, `REST_API_DB_PORT` |
| Release QC + Packaging | `production` | `REST_API_CLOUD_DB_HOST`, `REST_API_CLOUD_DB_NAME`, `REST_API_CLOUD_DB_USER`, `REST_API_CLOUD_DB_PASSWORD`, `REST_API_CLOUD_DB_PORT` |

`REST_API_DB_URL` is **not** a secret. QC builds `jdbc:postgresql://localhost:<PORT>/<NAME>` after Docker Postgres starts. Do not treat `REST_API_CLOUD_DB_*` as guest CD config (that is `heavy-rental/rest` on the instance).

Caller jobs must use an explicit `secrets:` map. Do not set `environment:` on a `uses:` job.

## Branch protection (application repo `develop`)

1. Integration *(highest priority)*
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
- ADRs 0004–0006: [`../../docs/adr/`](../../docs/adr/)
