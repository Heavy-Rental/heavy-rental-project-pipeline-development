# Delta for rest-ci-integration

## Purpose

Highest-priority gate: fetch the Spring REST API, install Java 21, resolve Maven dependencies, and prove project layout. Integration does not start Postgres.

On Integration CI the job id is `integration-check` and the check name is **Integration Check** (so it is not confused with `environment: integration`). Fast Feedback and Release keep job id `integration` and name **Integration**.

## ADDED Requirements

### Requirement: Integration is first
On Integration CI, the Integration Check job SHALL run only after the caller gate succeeds and SHALL always run (it SHALL NOT be skipped with `if:`). Quality Control, Security Testing, and CodeQL SHALL declare `needs: [integration-check]`. On Fast Feedback and Release, the Integration job SHALL run only after the caller gate succeeds. On Release, Quality Control and Packaging SHALL declare a dependency on Integration.

#### Scenario: Failed Integration Check blocks later CI jobs
- GIVEN Integration Check fails on Integration CI
- WHEN the workflow continues
- THEN Quality Control, Security Testing, and CodeQL do not start
- AND the GitHub Flow CI Gate still runs and fails

#### Scenario: Failed Integration blocks Release packaging
- GIVEN Integration fails on Release
- WHEN the workflow continues
- THEN Quality Control, Packaging, DAST, and Publish do not start

### Requirement: Java 21
When Maven/layout run, Integration SHALL install Temurin JDK 21 and SHALL use that JDK for Maven.

#### Scenario: Toolchain version
- GIVEN Integration has checked out the application
- AND Maven/layout are not skipped
- WHEN Java is set up
- THEN the runner Java version is 21

### Requirement: Maven wrapper is mandatory
When Maven/layout run, Integration SHALL fail if `mvnw` is missing. When the wrapper exists, Integration SHALL make it executable and invoke `./mvnw -B -ntp dependency:resolve dependency:resolve-plugins`. On Integration CI pull_request, those Maven/layout steps SHALL be skipped when Fast Feedback already succeeded for the PR head SHA.

#### Scenario: Wrapper present
- GIVEN the application contains `mvnw`
- AND Maven/layout are not skipped
- WHEN Integration prepares the environment
- THEN `mvnw` is executable
- AND dependency resolve runs

#### Scenario: Wrapper missing
- GIVEN the application does not contain `mvnw`
- AND Maven/layout are not skipped
- WHEN Integration prepares the environment
- THEN the job fails with an error that the Maven wrapper is required

#### Scenario: PR skips Maven when Fast Feedback succeeded
- GIVEN Integration Check on a pull_request
- AND Fast Feedback succeeded for the PR head SHA
- WHEN Integration Check continues
- THEN Maven wrapper, dependency resolve, and layout steps are skipped
- AND the job still succeeds

### Requirement: Project layout
When Maven/layout run, Integration SHALL verify the application root contains `pom.xml`, `mvnw`, `src/main/java`, and `src/main/resources`.

#### Scenario: Required files present
- GIVEN a checkout of the Spring REST API
- AND Maven/layout are not skipped
- WHEN layout checks run
- THEN each required path exists
- AND the job succeeds

#### Scenario: Required file missing
- GIVEN any required path is absent
- AND Maven/layout are not skipped
- WHEN layout checks run
- THEN the job fails

### Requirement: No database on Integration
Integration SHALL NOT start Postgres and SHALL NOT read `REST_API_DB_*` or `REST_API_CLOUD_DB_*`.

#### Scenario: No container
- GIVEN Integration runs
- WHEN the job finishes
- THEN no `postgres` container was started by this job

### Requirement: Fingerprint artifact
Integration SHALL upload `pom.xml` as a short-lived fingerprint artifact after checkout. On Integration CI this SHALL still run when Fast Feedback reuse skipped Maven/layout.

#### Scenario: Fingerprint uploaded
- GIVEN Integration checked out the application
- WHEN Integration finishes
- THEN an artifact containing `pom.xml` is uploaded
