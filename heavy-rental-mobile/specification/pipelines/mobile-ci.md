# Mobile CI family

**Application:** https://github.com/Heavy-Rental/heavy-rental-mobile  
**Authoring tree:** `heavy-rental-mobile/` in this pipeline-development repo  
**Stack:** Android / Kotlin (JVM 17) / Jetpack Compose / Gradle wrapper (app-declared; documented as 9.6.1 when this spec was written) / OpenAPI mocks on `:8081`

Workflows call `./gradlew`. They do not pin a Gradle version in YAML; the wrapper in the application repo is the source of truth.

This family validates the app and produces an unsigned APK. There is **no Academy CD** and no GHCR image.

## GitHub Flow

```
feature branch push  →  Fast Feedback (Integration only)
PR / push → develop  →  Integration CI (full gates, no packaging)
workflow_dispatch     →  Release (master + QC + APK + MobSF + GitHub Release)
```

Do **not** `uses:` `fast-feedback-pipeline.yml` from `mobile-ci-caller.yml`. Copy both Integration files into the mobile repo and call `./.github/workflows/integration-pipeline.yml`.

On `pull_request`, Integration looks up `mobile-fast-feedback-caller.yml` for the head SHA (`gh run list`). A successful run skips Android SDK / Gradle wrapper / `:app:preBuild` / layout. An in-flight run is waited on with `gh run watch`. The pending-run `jq` filter is inlined in the `PENDING_ID` / `PENDING_URL` `jq_field` calls (same quoting as `SUCCESS_ID`). Do not assign `PENDING_FILTER` and interpolate it — that construction breaks the wait. Push to `develop` and `workflow_dispatch` always run Integration locally. Fast Feedback does not subscribe to `pull_request`.

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

Release adds **Packaging** (`assembleRelease` unsigned APK) after Integration + QC + Security + CodeQL. Release does **not** run Mock Contract Tests.

## Android tools

| Concern | Tool |
| --- | --- |
| JDK | Temurin 17 (`JAVA_VERSION: "17"`) |
| Android SDK | `compileSdk` / build-tools **35** (`ANDROID_COMPILE_SDK`, `ANDROID_BUILD_TOOLS`) |
| Build | Gradle wrapper (`./gradlew --no-daemon`) |
| QC | `:app:lintDebug` + `:app:testDebugUnitTest` + `:app:assembleDebug` |
| Mocks | Node scripts `mock:prepare` / `mock:prism` / `mock:verify` on `:8081` |
| SAST / SCA | Semgrep `p/kotlin` `p/java` + OWASP / audit / secrets / CWE Top 25 / FindSecBugs / Gitleaks / SQL injection / JWT / insecure-transport, plus custom ERROR rules for plaintext credentials (reports: `semgrep.sarif` + `semgrep.json` + `semgrep.txt`, ERROR-only gate); Trivy FS SARIF |
| Human security report | Combined PDF artifact `security-combined-report-pdf`; download from the PR Checks tab (workflow Summary → Artifacts, or Security Testing job summary) |
| Human DAST report | Combined PDF artifact `dast-combined-report-pdf` (`dast-reports/combined-dast-report.pdf`); download from the Release run Summary → Artifacts, the DAST job summary link, or the GitHub Release |
| Code scanning | CodeQL `java-kotlin` |
| Package | `:app:assembleRelease` unsigned APK |

## GitHub Actions

Floating major tags (ADR 0005; same style as REST/portal CI). Pins must match the YAML `uses:` lines.

| Action | Pin |
| --- | --- |
| `actions/checkout` | v7 |
| `actions/setup-java` | v6 |
| `actions/setup-node` | v7 |
| `actions/setup-python` | v7 |
| `actions/cache` | v6 |
| `actions/upload-artifact` | v7 |
| `actions/download-artifact` | v8 |
| `actions/github-script` | v9 |
| `android-actions/setup-android` | v4 |
| `aquasecurity/trivy-action` | v0.36.0 |
| `github/codeql-action` (`init`, `analyze`, `upload-sarif`) | v4 |

No repository secrets are required for v1.

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

`DEFAULT_APP_REPOSITORY` is `Heavy-Rental/heavy-rental-mobile`. When the caller runs **in** the app repo, checkout is the calling repo (into `app/`).

## Pipeline boundaries

| Concern | In this family? |
| --- | --- |
| Fast Feedback, Integration CI, unsigned Release APK | Yes |
| Env-driven Docker image / GHCR | No — not a container family |
| Emulator / `connectedAndroidTest` | No |
| Play signing, keystore, Firebase App Distribution | No |
| GHCR / Docker | No |
| Live Spring Boot | No |
| Academy app CD / infra / operate | No |

## Specs

- OpenSpec: [`../../openspec/changes/add-mobile-ci-pipeline/`](../../openspec/changes/add-mobile-ci-pipeline/)
- OpenSPDD: [`../../spdd/analysis/add-mobile-ci-pipeline.md`](../../spdd/analysis/add-mobile-ci-pipeline.md)
- ADRs: [`../../docs/adr/`](../../docs/adr/)
