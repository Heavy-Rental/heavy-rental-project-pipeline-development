# Delta for rest-ci-integration

## Purpose

Highest-priority gate: fetch the Spring REST API, install Java 21, resolve Maven dependencies, and prove project layout. Integration does not start Postgres.

## ADDED Requirements

### Requirement: Integration is first
The Integration job SHALL run only after the caller gate succeeds. Quality Control, Security Testing, CodeQL, and Packaging SHALL declare a dependency on Integration.

#### Scenario: Failed Integration blocks later jobs
- GIVEN Integration fails
- WHEN the workflow continues
- THEN Quality Control, Security Testing, CodeQL, and Packaging do not start
- AND the GitHub Flow CI Gate (when present) still runs and fails

### Requirement: Java 21
Integration SHALL install Temurin JDK 21 and SHALL use that JDK for Maven.

#### Scenario: Toolchain version
- GIVEN Integration has checked out the application
- WHEN Java is set up
- THEN the runner Java version is 21

### Requirement: Maven wrapper is mandatory
Integration SHALL fail if `mvnw` is missing. When the wrapper exists, Integration SHALL make it executable and invoke `./mvnw -B -ntp dependency:resolve dependency:resolve-plugins`.

#### Scenario: Wrapper present
- GIVEN the application contains `mvnw`
- WHEN Integration prepares the environment
- THEN `mvnw` is executable
- AND dependency resolve runs

#### Scenario: Wrapper missing
- GIVEN the application does not contain `mvnw`
- WHEN Integration prepares the environment
- THEN the job fails with an error that the Maven wrapper is required

### Requirement: Project layout
Integration SHALL verify the application root contains `pom.xml`, `mvnw`, `src/main/java`, and `src/main/resources`.

#### Scenario: Required files present
- GIVEN a checkout of the Spring REST API
- WHEN layout checks run
- THEN each required path exists
- AND the job succeeds

#### Scenario: Required file missing
- GIVEN any required path is absent
- WHEN layout checks run
- THEN the job fails

### Requirement: No database on Integration
Integration SHALL NOT start Postgres and SHALL NOT read `REST_API_DB_*` or `REST_API_CLOUD_DB_*`.

#### Scenario: No container
- GIVEN Integration runs
- WHEN the job finishes
- THEN no `postgres` container was started by this job

### Requirement: Fingerprint artifact
Integration SHALL upload `pom.xml` as a short-lived fingerprint artifact.

#### Scenario: Fingerprint uploaded
- GIVEN layout checks passed
- WHEN Integration finishes
- THEN an artifact containing `pom.xml` is uploaded
