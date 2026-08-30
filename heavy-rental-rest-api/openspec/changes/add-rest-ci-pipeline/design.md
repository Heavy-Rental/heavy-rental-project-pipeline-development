# Design: REST API GitHub Actions CI family (as-implemented)

## Context

The Spring REST API already has reusable-caller Fast Feedback, Integration CI, and Release workflows under `heavy-rental-rest-api/`. Academy CD is a separate family (`deploy-pipeline/`). This document describes the CI family as the YAML behaves today.

## Goals / Non-Goals

**Goals:**

- Same GitHub Flow as Haystack / portal / mobile (fast feedback / CI / dispatch-only release).
- Integration Check first on Integration CI; later jobs `needs: [integration-check]`. Fast Feedback and Release keep job `integration`.
- PR Integration Check reuses a successful Fast Feedback run for the head SHA (waits if in-flight; CI caller does not `uses:` Fast Feedback).
- Java 21 + Maven wrapper + Docker Postgres for QC tests.
- SARIF 2.1.0 for Semgrep (app + GHA) and Trivy; CodeQL `java-kotlin` on **Integration CI only**.
- Release artifacts consumable by Academy CD (WAR + env-driven Tomcat image tar; Publish pushes GHCR and creates the GitHub Release). DAST runs between Packaging and Publish.

**Non-Goals:**

- Hitting live Academy RDS from CI
- Terraform / compose / operate
- Unifying Integration CI / Release `DEFAULT_APP_REPOSITORY` (`Heavy-Rental/...`) with Fast Feedback (`SA62-team1/...` act fallback)

## Decisions

1. **Reusable + caller gate.** Sole callers: `rest-api-fast-feedback-caller.yml`, `rest-api-ci-caller.yml`, `rest-api-release-caller.yml`. Integration CI caller `uses:` `./.github/workflows/integration-pipeline.yml` (copy both files into the Spring repo). It does not `uses:` Fast Feedback.
2. **Java 21 Temurin + `./mvnw`.** Integration resolves deps and checks `pom.xml`, `mvnw`, `src/main/java`, `src/main/resources`, unless Integration Check reused Fast Feedback.
3. **Same `REST_API_DB_*` names, two Environments, two caller maps.** Integration QC: Environment `integration` plus an explicit caller secrets map from **Repository** secrets. Release QC: Environment `production` plus the same explicit caller map from **Repository** secrets. Both start a **local** Docker Postgres. `REST_API_DB_URL` is derived. Neither is guest CD config. No `secrets: inherit`.
4. **QC package is not deploy.** Integration CI uploads WAR as build verification.
5. **Release Packaging** rebuilds the WAR, stages versioned + stable names, builds `tomcat:10.1-jdk21-temurin` + `ROOT.war`, and uploads the tar. The image is env-driven (ADR 0007): no baked `POSTGRES_*` / `SPRING_DATASOURCE_*` / `HAYSTACK_*` / Stripe / JWT. `spring-datasource.env` is a workflow artifact only (no password) and is not copied into the image. SAST/CodeQL are not Release jobs.
6. **DAST then Publish.** DAST loads the tar (ZAP + Dastardly gates, Nuclei report-only, combined PDF). Publish pushes GHCR and creates the GitHub Release. The caller is `workflow_dispatch` only; it must not use `on: release`.
7. **CI family stops at packaging / GHCR.** Compose lives in the CD family.
8. **QC Environments are hardcoded** (`integration` / `production`). Callers pass `github_environment`; the reusable jobs do not read that input.
9. **Semgrep is two passes.** Application packs exclude `.github/**`. GHA pass allows secrets-context maps and forbids `secrets: inherit` except the paid CD caller.

## Risks / Trade-offs

| Risk | Mitigation |
| --- | --- |
| Treating Release QC Postgres as guest SM | PREPARE + `rest-ci-scope` + ADR 0005 |
| `environment:` on a `uses:` job | Invalid; both callers forward Repository secrets via an explicit map; QC jobs still use Environment `integration` / `production`; no inherit |
| Empty Integration or Release QC secrets | Repository secrets required for both caller maps (a `uses:` job cannot read Environment secrets) |
| `p/secrets` flags workflow maps | App Semgrep excludes `.github/**`; GHA pass uses custom inherit / hardcoded-secret rules |
| `p/spring` Semgrep 404 | YAML already uses `p/java` + OWASP |

## Open Questions

None. This change documents shipped YAML.
