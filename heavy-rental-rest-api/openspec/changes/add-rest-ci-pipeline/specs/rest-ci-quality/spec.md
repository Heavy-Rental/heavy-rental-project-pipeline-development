# Delta for rest-ci-quality

## Purpose

Compile-time quality for the Spring REST API: compile, unit/Spring tests against a local Docker Postgres, and package WAR as build verification.

## ADDED Requirements

### Requirement: Quality Control needs Integration
Quality Control SHALL run only after Integration succeeds and SHALL check out the same application source Integration resolved.

#### Scenario: Same checkout mode
- GIVEN Integration published `checkout_mode`, `app_repository`, and `app_ref`
- WHEN Quality Control starts
- THEN it checks out the application using those outputs

### Requirement: Integration CI uses Environment integration
On the Integration CI reusable workflow, Quality Control SHALL set `environment: integration` and SHALL require secrets `REST_API_DB_NAME`, `REST_API_DB_USER`, `REST_API_DB_PASSWORD`, and `REST_API_DB_PORT`.

#### Scenario: Missing integration secret fails
- GIVEN any of `REST_API_DB_NAME`, `REST_API_DB_USER`, `REST_API_DB_PASSWORD`, `REST_API_DB_PORT` is empty
- WHEN Quality Control verifies secrets
- THEN the job fails before starting Postgres

### Requirement: Release uses Environment production
On the Release reusable workflow, Quality Control SHALL set `environment: production` and SHALL require `REST_API_CLOUD_DB_HOST`, `REST_API_CLOUD_DB_NAME`, `REST_API_CLOUD_DB_USER`, `REST_API_CLOUD_DB_PASSWORD`, and `REST_API_CLOUD_DB_PORT`.

#### Scenario: Missing cloud secret fails
- GIVEN any required `REST_API_CLOUD_DB_*` secret is empty
- WHEN Release Quality Control verifies secrets
- THEN the job fails before starting Postgres

### Requirement: Local Docker Postgres for tests
Quality Control SHALL start `postgres:16-alpine` on the runner, wait until it accepts connections, run `./mvnw test` against `jdbc:postgresql://localhost:<PORT>/<NAME>`, and stop the container even when tests fail. Tests SHALL bind the datasource password through env, not the Maven CLI.

#### Scenario: Happy path
- GIVEN secrets are present and tests pass
- WHEN Quality Control runs
- THEN Postgres starts
- AND Maven tests exit 0
- AND the container is removed

#### Scenario: Failing test
- GIVEN a Spring test fails
- WHEN Quality Control runs
- THEN the job fails
- AND the Postgres container is still removed

### Requirement: REST_API_DB_URL is derived
Quality Control SHALL NOT require `REST_API_DB_URL` as a secret. It SHALL write `jdbc:postgresql://localhost:<PORT>/<NAME>` to `GITHUB_ENV` after Postgres starts (no password in the URL).

#### Scenario: URL built after start
- GIVEN `REST_API_DB_PORT` and `REST_API_DB_NAME` are set
- WHEN Postgres has started
- THEN `REST_API_DB_URL` is `jdbc:postgresql://localhost:<PORT>/<NAME>`

### Requirement: Package WAR is build verification
Quality Control SHALL run `./mvnw -DskipTests package` and SHALL fail if `target/` contains no `.war` or `.jar`. On Integration CI this artifact is not a deploy.

#### Scenario: WAR produced
- GIVEN tests passed
- WHEN package runs
- THEN at least one `.war` or `.jar` exists under `target/`
