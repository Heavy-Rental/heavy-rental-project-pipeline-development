# ADR 0007: REST Release image takes guest config from the environment

- **Status:** Accepted
- **Date:** 2026-08-18
- **Change:** `add-rest-ci-pipeline` (image contract)
- **Related:** [0005](0005-rest-ci-secret-environments.md), [0006](0006-rest-ci-stops-at-packaging.md)

## Context

Academy compose runs the Release Tomcat image with `env_file: .env` from `heavy-rental/rest` (Postgres aliases, `HAYSTACK_BASE_URL`, Stripe). Baking `REST_API_CLOUD_DB_*` or a JDBC URL into the image would pin every tag to one QC host. The `spring-datasource.env` workflow artifact is a deploy helper without a password; it is not the Academy contract.

## Decision

Release Packaging generates (or accepts) a Dockerfile with **no** `ENV`/`ARG` for `POSTGRES_*`, `SPRING_DATASOURCE_*`, `HAYSTACK_*`, `STRIPE_*`, `APP_JWT_*`, or `REST_API_*`, and no `.env` copy. After `docker build`, it inspects `Config.Env` and runs the image with **dummy** datasource / Haystack / Stripe / JWT values to prove they are visible. It does not start Tomcat or connect to RDS.

## Consequences

- The same image tag works on any Academy lab once CD injects SM.
- An app `Dockerfile` that bakes `SPRING_DATASOURCE_URL` fails Packaging.
- `REST_API_CLOUD_DB_*` stay on Environment `production` for QC only.
