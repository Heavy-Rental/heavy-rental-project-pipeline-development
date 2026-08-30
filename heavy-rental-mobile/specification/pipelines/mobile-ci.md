# Mobile CI family

**Application:** https://github.com/Heavy-Rental/heavy-rental-mobile  
**Authoring tree:** `heavy-rental-mobile/` in this pipeline-development repo  
**Stack:** Android / Kotlin (JVM 17) / Jetpack Compose / Gradle wrapper (app-declared; documented as 9.6.1 when this spec was written) / OpenAPI Mockoon on `:8081`

Workflows call `./gradlew`. They do not pin a Gradle version in YAML; the wrapper in the application repo is the source of truth.

This family validates the app and produces an unsigned APK, then MobSF DAST and a GitHub Release. There is **no Academy CD** and no GHCR image.

## GitHub Flow

```
feature branch push  →  Fast Feedback (Integration only)
PR / push → develop  →  Integration CI (reuses Fast Feedback on PR, waits if in-flight; full gates, no packaging)
workflow_dispatch     →  Release (master + QC + APK + MobSF + GitHub Release)
```

Do **not** `uses:` `fast-feedback-pipeline.yml` from `mobile-ci-caller.yml`. Copy both Integration files into the mobile repo and call `./.github/workflows/integration-pipeline.yml`.

On `pull_request`, Integration looks up `mobile-fast-feedback-caller.yml` for the head SHA (`gh run list`). A successful run skips Android SDK / Gradle wrapper / `:app:preBuild` / layout. An in-flight run is waited on with `gh run watch`. The pending-run `jq` filter is inlined in the `PENDING_ID` / `PENDING_URL` `jq_field` calls (same quoting as `SUCCESS_ID`). Do not assign `PENDING_FILTER` and interpolate it — that construction breaks the wait. Push to `develop` and `workflow_dispatch` always run Integration locally. Fast Feedback does not subscribe to `pull_request`.

## Job graph (Integration CI)

```
assert-caller
      │
      ▼
 Integration          PR: reuse Fast Feedback for the head SHA (skip Android SDK / Gradle / layout)
                      else: JDK 17 + Android SDK + Gradle wrapper + :app:preBuild + layout
      │
      ├── Quality Control         lintDebug + testDebugUnitTest + assembleDebug
      ├── Security Testing        Semgrep + Trivy (SARIF) + combined PDF
      ├── CodeQL Analysis         java-kotlin
      └── Mock Contract Tests     mock:mockoon + mock:verify (required; optional mock:prepare)
      │
      ▼
 GitHub Flow CI Gate
```

## Job graph (Release)

SAST, CodeQL, and Mock Contract Tests stay on Integration CI (`develop`). Release does **not** rerun them. The caller is `workflow_dispatch` only (it **creates** the GitHub Release; it must not use `on: release`). Always checkout **`master`**.

```
assert-caller
      │
      ▼
 Integration          checkout master, JDK 17 + Android SDK + Gradle, layout
      │
      ▼
 Quality Control      lintDebug + testDebugUnitTest + assembleDebug
      │
      ▼
 Packaging            unsigned assembleRelease (needs Integration + QC only)
      │
      ▼
 DAST                 MobSF static scan of the APK + combined-dast-report.pdf
      │
      ▼
 Publish              GitHub Release on master (unsigned APKs + DAST reports; no GHCR)
```

## Android tools

| Concern | Tool |
| --- | --- |
| JDK | Temurin 17 (`JAVA_VERSION: "17"`) |
| Android SDK | `compileSdk` / build-tools **35** (`ANDROID_COMPILE_SDK`, `ANDROID_BUILD_TOOLS`) |
| Build | Gradle wrapper (`./gradlew --no-daemon`) |
| QC | `:app:lintDebug` + `:app:testDebugUnitTest` + `:app:assembleDebug` |
| Mocks | Node scripts `mock:mockoon` + `mock:verify` on `:8081` (optional `mock:prepare`; `MOCK_EXPECT_ECHO=1`; fail if Mockoon/verify missing; Prism is not used in CI) |
| SAST / SCA | Semgrep `p/kotlin` `p/java` + OWASP / audit / secrets / CWE Top 25 / FindSecBugs / Gitleaks / SQL injection / JWT / insecure-transport, plus custom ERROR rules for plaintext credentials (report: `semgrep.sarif`, ERROR-only gate); Trivy FS SARIF |
| Human security report | Combined PDF artifact `security-combined-report-pdf`; download from the PR Checks tab (workflow Summary → Artifacts, or Security Testing job summary) |
| Human DAST report | Combined PDF artifact `dast-combined-report-pdf` (`dast-reports/combined-dast-report.pdf`); download from the Release run Summary → Artifacts, the DAST job summary link, or the GitHub Release |
| Code scanning | CodeQL `java-kotlin` |
| Package | `:app:assembleRelease` unsigned APK |
| DAST | MobSF static scan of the unsigned APK (Release only). High-severity heuristic is a **warning**, not a fail |
| Publish | `gh release create` on `master` (no GHCR) |

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

No repository secrets are required for v1. Integration CI requests `checks: write` so the combined security PDF can appear on the PR Checks tab. Release requests `contents: write` (GitHub Release) and does **not** request `packages: write`.

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

Checkout is the calling repository into `app/` (Fast Feedback / Integration: `github.sha`). Release always checks out **`master`** and ignores `app_ref`. Env `DEFAULT_APP_REPOSITORY` is set to `Heavy-Rental/heavy-rental-mobile` but is **not interpolated**. The Release caller does not pass `app_repository` / `app_ref`.

## Pipeline boundaries

| Concern | In this family? |
| --- | --- |
| Fast Feedback, Integration CI, unsigned Release APK, MobSF DAST, GitHub Release | Yes |
| Env-driven Docker image / GHCR | No — not a container family |
| Emulator / `connectedAndroidTest` | No |
| Play signing, keystore, Firebase App Distribution | No |
| GHCR / Docker | No |
| Live Spring Boot | No |
| Academy app CD / infra / operate | No |

## Specs

- OpenSpec: [`../../openspec/changes/add-mobile-ci-pipeline/`](../../openspec/changes/add-mobile-ci-pipeline/)
- OpenSPDD: [`../../spdd/analysis/add-mobile-ci-pipeline.md`](../../spdd/analysis/add-mobile-ci-pipeline.md)
- ADRs: [`../../docs/adr/`](../../docs/adr/) (0001–0007)
