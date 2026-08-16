# Mobile CI family

**Application:** https://github.com/Heavy-Rental/heavy-rental-mobile  
**Stack:** Android / Kotlin (JVM 17) / Jetpack Compose / Gradle wrapper 9.6.1 / OpenAPI mocks on `:8081`

## GitHub Flow

```
feature branch push  →  Fast Feedback (Integration only)
PR / push → develop  →  Integration CI (full gates, no packaging)
develop → master PR or published GitHub Release
                     →  Release (full gates + unsigned APK)
```

## Job graph (Integration CI)

```
assert-caller
      │
      ▼
 Integration
      │
      ├── Quality Control         lintDebug + testDebugUnitTest + assembleDebug
      ├── Security Testing        Semgrep + Trivy (SARIF)
      ├── CodeQL Analysis         java-kotlin
      └── Mock Contract Tests     mock:prepare + Prism + mock:verify
      │
      ▼
 GitHub Flow CI Gate
```

Release adds **Packaging** (`assembleRelease` unsigned APK) after Integration + QC + Security + CodeQL.

## Branch protection (application repo `develop`)

Require these check names:

1. Integration *(highest priority)*
2. Quality Control
3. Security Testing
4. CodeQL Analysis
5. Mock Contract Tests
6. GitHub Flow CI Gate

## Local validation (this repo)

```bash
actionlint heavy-rental-mobile/fast-feedback-ci-pipeline/fast-feedback-pipeline.yml
actionlint heavy-rental-mobile/fast-feedback-ci-pipeline/mobile-fast-feedback-caller.yml
actionlint heavy-rental-mobile/integration-pipeline/integration-pipeline.yml
actionlint heavy-rental-mobile/integration-pipeline/mobile-ci-caller.yml
actionlint heavy-rental-mobile/release-pipeline/release-pipeline.yml
actionlint heavy-rental-mobile/release-pipeline/mobile-release-caller.yml

# Local act smoke (caller gate). See heavy-rental-mobile/act/README.md
./heavy-rental-mobile/act/run-act.sh smoke
```

## Install into the application repo

Copy each pair into `Heavy-Rental/heavy-rental-mobile`:

```
.github/workflows/mobile-fast-feedback-caller.yml
.github/workflows/fast-feedback-pipeline.yml
.github/workflows/mobile-ci-caller.yml
.github/workflows/integration-pipeline.yml
.github/workflows/mobile-release-caller.yml
.github/workflows/release-pipeline.yml
```

No repository secrets are required for v1.

## Out of scope (v1)

Emulator tests, Play signing, GHCR, live Spring Boot, `overall-project-deploy-pipeline`.
