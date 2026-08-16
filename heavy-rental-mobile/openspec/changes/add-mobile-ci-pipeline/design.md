# Design: Mobile GitHub Actions CI family

## Context

This pipeline-development repo already authors REST API and web-portal workflows as **reusable `workflow_call` files + sole-allowed callers**. The mobile application is Kotlin/Compose on JDK 17, Gradle wrapper 9.6.1, `compileSdk` 35, with JVM unit tests under `app/src/test` and Node mock tooling (`mock:prepare`, `mock:prism`, `mock:verify`) on port 8081.

## Goals / Non-Goals

**Goals:**

- Same GitHub Flow family as REST/portal (fast feedback / CI / release).
- Integration is the highest-priority job; later jobs `needs: [integration]`.
- Android-appropriate toolchain: JDK 17 Temurin + Android SDK on `ubuntu-latest`.
- JVM lint/test/assemble as Quality Control; Prism mock verify as the contract analog of portal REST tests.
- Semgrep-safe scripts (bind `github.*` / `inputs.*` through `env:`).

**Non-Goals:**

- Emulator / `connectedAndroidTest`
- Signed Play artifacts, keystore secrets, Firebase App Distribution
- GHCR or Docker images
- Hitting a live Spring Boot backend
- Changing the Android product `specification/` in the application repo

## Decisions

1. **Reusable + caller gate.** Copy the REST/portal model. Each reusable file rejects any `github.workflow_ref` that is not its matching caller.
2. **JDK 17, not 21.** Matches `app/build.gradle.kts` (`JavaVersion.VERSION_17`, `jvmTarget = "17"`). REST API stays on 21; do not share that constant.
3. **`android-actions/setup-android@v3`** for SDK + license acceptance; install `platforms;android-35` and a 35.x build-tools package.
4. **No GitHub Environment / secrets on QC.** Mobile tests do not need Postgres.
5. **Mock job uses `mock:prism` (headless) + `mock:verify`.** Skip cleanly only when those scripts are absent from `package.json`.
6. **Release APK is unsigned.** Stage versioned + stable filenames. AAB only if `assembleRelease` already produces one.
7. **Specs and YAML live under `heavy-rental-mobile/`.** OpenSpec, OpenSPDD, and workflow files stay with the pipeline they describe.

## Risks / Trade-offs

| Risk | Mitigation |
| --- | --- |
| Android SDK download makes Integration slower than Node/Java siblings | Cache SDK + Gradle; keep fast-feedback Integration-only |
| `debugCompileClasspath` name may differ | Prefer `:app:preBuild` / wrapper + `help` so Integration does not fail on configuration naming |
| Semgrep `p/kotlin` registry drift | Same two-pass pattern as siblings (SARIF always, ERROR gate); fail with a clear message if the ruleset 404s |
| Unsigned APK is not store-ready | Document as v1; signing is a later OpenSpec change |
| First-time Gradle on the runner is slow | `actions/setup-java` Gradle cache + `--no-daemon` |

## Migration Plan

1. Land specs + YAML in this repo.
2. Copy the six workflow files into `Heavy-Rental/heavy-rental-mobile` `.github/workflows/`.
3. Require the named jobs on `develop` branch protection.
4. Archive this OpenSpec change once the install copy is accepted.

## Open Questions

None for v1. Signing, emulator tests, and GHCR are deferred on purpose.
