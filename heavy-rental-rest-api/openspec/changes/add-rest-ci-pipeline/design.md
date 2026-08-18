# Design: REST API GitHub Actions CI family (as-implemented)

## Context

The Spring REST API already has reusable-caller Fast Feedback, Integration CI, and Release workflows under `heavy-rental-rest-api/`. Academy CD is a separate family (`deploy-pipeline/`). This document describes the CI family as the YAML behaves today.

## Goals / Non-Goals

**Goals:**

- Same GitHub Flow as Haystack / portal / mobile (fast feedback / CI / release).
- Integration first; later jobs `needs: [integration]`.
- Java 21 + Maven wrapper + Docker Postgres for QC tests.
- SARIF 2.1.0 for Semgrep and Trivy; CodeQL `java-kotlin`.
- Release artifacts consumable by Academy CD (WAR + env-driven Tomcat image tar; GHCR off PR).

**Non-Goals:**

- Changing existing YAML
- Hitting live Academy RDS from CI
- Terraform / compose / operate
- Replacing `SA62-team1/...` `DEFAULT_APP_REPOSITORY` (act fallback)

## Decisions

1. **Reusable + caller gate.** Sole callers: `rest-api-fast-feedback-caller.yml`, `rest-api-ci-caller.yml`, `rest-api-release-caller.yml`.
2. **Java 21 Temurin + `./mvnw`.** Integration resolves deps and checks `pom.xml`, `mvnw`, `src/main/java`, `src/main/resources`.
3. **Same `REST_API_DB_*` names, two Environments.** Integration QC: Environment `integration`. Release QC: Environment `production`. Both start a **local** Docker Postgres. `REST_API_DB_URL` is derived. Neither is guest CD config.
4. **QC package is not deploy.** Integration CI uploads WAR as build verification.
5. **Release Packaging** rebuilds the WAR, stages versioned + stable names, builds `tomcat:10.1-jdk21-temurin` + `ROOT.war`, uploads tar, pushes GHCR when not a pull request. The image is env-driven (ADR 0007): no baked `POSTGRES_*` / `SPRING_DATASOURCE_*` / `HAYSTACK_*` / Stripe / JWT. `spring-datasource.env` is a workflow artifact only (no password) and is not copied into the image.
6. **CI family stops at packaging.** Compose lives in the CD family.

## Risks / Trade-offs

| Risk | Mitigation |
| --- | --- |
| Treating Release QC Postgres as guest SM | PREPARE + `rest-ci-scope` + ADR 0005 |
| `environment:` on a `uses:` job | Invalid; secrets map on the caller only |
| `p/spring` Semgrep 404 | YAML already uses `p/java` + OWASP |

## Open Questions

None. This change documents shipped YAML.
