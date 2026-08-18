# ADR 0002: Mobile CI uses JDK 17, not 21

- **Status:** Accepted
- **Date:** 2026-08-17
- **Change:** `add-mobile-ci-pipeline`

## Context

The REST API family uses Java 21. The Android app declares `JavaVersion.VERSION_17` / `jvmTarget = "17"`. Sharing the REST constant would break compile.

## Decision

All mobile workflows set `JAVA_VERSION: "17"` (Temurin). Android SDK install uses `compileSdk` 35 and build-tools 35.x. Builds go through `./gradlew --no-daemon`.

## Consequences

- Do not reuse REST `JAVA_VERSION`.
- Gradle version is whatever the application wrapper ships; YAML does not pin 9.6.1.
