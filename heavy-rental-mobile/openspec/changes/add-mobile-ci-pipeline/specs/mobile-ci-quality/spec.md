# Delta for mobile-ci-quality

## Purpose

Compile-time quality for the Android app: Android Lint, JVM unit tests, and a debug APK. No emulator and no database secrets.

## ADDED Requirements

### Requirement: Quality Control needs Integration
Quality Control SHALL run only after Integration succeeds and SHALL check out the same application source Integration resolved.

#### Scenario: Same checkout mode
- GIVEN Integration published `checkout_mode`, `app_repository`, and `app_ref`
- WHEN Quality Control starts
- THEN it checks out the application using those outputs

### Requirement: Lint, unit tests, and debug assemble
Quality Control SHALL run Android Lint for the debug variant, JVM unit tests for the debug variant, and `assembleDebug`. It SHALL NOT start an Android emulator or run instrumented `connectedAndroidTest` tasks.

#### Scenario: Happy path
- GIVEN the application compiles and its JVM tests pass
- WHEN Quality Control runs Gradle
- THEN `:app:lintDebug`, `:app:testDebugUnitTest`, and `:app:assembleDebug` complete successfully
- AND no emulator is started

#### Scenario: Failing unit test
- GIVEN a JVM unit test fails
- WHEN Quality Control runs
- THEN the job fails

### Requirement: No secrets or Environments
Quality Control SHALL NOT require GitHub Environments or repository secrets.

#### Scenario: No database secrets
- GIVEN Quality Control starts
- WHEN the job is configured
- THEN it does not read `REST_API_DB_*` or any other database secret
- AND it does not set `environment:`

### Requirement: Reports and debug APK
Quality Control SHALL upload lint reports, unit-test XML results, and the debug APK as artifacts even when tests fail (reports use `if: always()`).

#### Scenario: Failed tests still publish reports
- GIVEN unit tests fail
- WHEN the job finishes
- THEN lint and test-result artifacts are still uploaded when those files exist
