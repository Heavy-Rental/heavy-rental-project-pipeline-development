# ADR 0007: REST Release image takes guest config from the environment

- **Status:** Accepted
- **Date:** 2026-08-18
- **Change:** `add-rest-ci-pipeline` (image contract)
- **Related:** [0005](0005-rest-ci-secret-environments.md), [0006](0006-rest-ci-stops-at-packaging.md)

## Context

Academy compose runs the Release Tomcat image with `env_file: .env` from `heavy-rental/rest` (Postgres aliases, `HAYSTACK_BASE_URL`, Stripe). Baking `REST_API_CLOUD_DB_*` or a JDBC URL into the image would pin every tag to one QC host. The `spring-datasource.env` workflow artifact is a deploy helper without a password; it is not the Academy contract.

## Decision

Release Packaging **always generates** `tomcat:10.1-jdk21-temurin` + `ROOT.war` (an app `Dockerfile` is not the deploy image) with `ENV SPRING_PROFILES_ACTIVE=prod` and **no** `ENV`/`ARG` for `POSTGRES_*`, `SPRING_DATASOURCE_*`, `HAYSTACK_*`, `STRIPE_*`, `APP_JWT_*`, or `REST_API_*`, and no `.env` copy. The WAR SHALL contain `application-prod.properties` (hyphen) for non-secret prod defaults. Secrets stay in `heavy-rental/rest`. After `docker build`, Packaging inspects `Config.Env` (must include `SPRING_PROFILES_ACTIVE=prod`), proves dummy datasource / Haystack / Stripe / JWT values are visible, confirms `ROOT.war` has `WEB-INF/`, and starts Tomcat only long enough to prove TCP `:8080` binds. It does not connect to RDS and does not require actuator 200.

## Consequences

- The same image tag works on Docker Desktop (`docker run -p 8080:8080 -e …`), compose, or any Academy lab once env is injected.
- An app `java -jar` Dockerfile is moved aside; it is not pushed to GHCR.
- `REST_API_CLOUD_DB_*` stay on Environment `production` for QC only.
