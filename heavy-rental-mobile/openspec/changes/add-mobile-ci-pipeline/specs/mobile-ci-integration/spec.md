# Delta for mobile-ci-integration

## Purpose

Highest-priority gate: fetch the Android application, install the toolchain, resolve Gradle, and prove the project layout.

## ADDED Requirements

### Requirement: Integration is first
The Integration job SHALL run only after the caller gate succeeds. Quality Control, Security Testing, CodeQL, Mock Contract Tests, and Packaging SHALL declare a dependency on Integration.

#### Scenario: Failed Integration blocks later jobs
- GIVEN Integration fails
- WHEN the workflow continues
- THEN Quality Control, Security Testing, CodeQL, Mock Contract Tests, and Packaging do not start
- AND the GitHub Flow CI Gate (when present) still runs and fails

### Requirement: JDK 17 Temurin
Integration SHALL install Eclipse Temurin JDK 17 and SHALL use that JDK for Gradle.

#### Scenario: Toolchain version
- GIVEN Integration has checked out the application
- WHEN Java is set up
- THEN the runner Java version is 17
- AND the distribution is Temurin

### Requirement: Android SDK for compileSdk 35
Integration SHALL install an Android SDK that can compile API 35 and SHALL accept the required SDK licenses.

#### Scenario: Platform present
- GIVEN JDK 17 is available
- WHEN the Android SDK is set up
- THEN `platforms;android-35` is installed
- AND SDK licenses are accepted so Gradle does not prompt

### Requirement: Gradle wrapper is mandatory
Integration SHALL fail if `gradlew` is missing. When the wrapper exists, Integration SHALL make it executable and invoke it with `--no-daemon`.

#### Scenario: Wrapper present
- GIVEN the application contains `gradlew`
- WHEN Integration prepares Gradle
- THEN `gradlew` is executable
- AND a subsequent Gradle invocation uses `--no-daemon`

#### Scenario: Wrapper missing
- GIVEN the application does not contain `gradlew`
- WHEN Integration prepares Gradle
- THEN the job fails with an error that the Maven-style wrapper equivalent (`gradlew`) is required

### Requirement: Project layout
Integration SHALL verify the Android application root contains `settings.gradle.kts`, `build.gradle.kts`, `gradlew`, `app/build.gradle.kts`, `specification/`, and `package.json`.

#### Scenario: Required files present
- GIVEN a checkout of Heavy Rental mobile
- WHEN layout checks run
- THEN each required path exists
- AND the job succeeds

#### Scenario: Required file missing
- GIVEN any required path is absent
- WHEN layout checks run
- THEN the job fails

### Requirement: Gradle cache and fingerprint
Integration SHALL cache Gradle dependencies via the Java setup action and SHALL upload a short-lived fingerprint of Gradle settings files.

#### Scenario: Fingerprint artifact
- GIVEN layout checks passed
- WHEN Integration finishes
- THEN an artifact containing `settings.gradle.kts` is uploaded
