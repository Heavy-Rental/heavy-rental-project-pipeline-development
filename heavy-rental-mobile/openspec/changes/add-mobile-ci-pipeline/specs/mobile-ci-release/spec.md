# Delta for mobile-ci-release

## Purpose

Release packaging produces unsigned, versioned Android APK artifacts after Integration and Quality Control. DAST scans the APK with MobSF. Publish creates the GitHub Release. There is no GHCR image. SAST, CodeQL, and Mock Contract Tests stay on Integration CI.

## ADDED Requirements

### Requirement: Packaging waits for Integration and Quality Control
Packaging SHALL run only after Integration and Quality Control have succeeded. It SHALL NOT need Security Testing, CodeQL, or Mock Contract Tests (those jobs are not on the Release workflow).

#### Scenario: QC red blocks packaging
- GIVEN Quality Control failed
- WHEN Packaging is evaluated
- THEN Packaging does not start

#### Scenario: SAST is not a Release job
- GIVEN the Release workflow job list
- WHEN Packaging is evaluated
- THEN no Security Testing, CodeQL, or Mock Contract Tests job is present
- AND Packaging `needs` only Integration and Quality Control

### Requirement: Unsigned release assemble
Packaging SHALL run `./gradlew --no-daemon :app:assembleRelease` and SHALL NOT require a keystore, Play credentials, or GitHub Environment secrets.

#### Scenario: Assemble without signing secrets
- GIVEN Quality Control already passed
- WHEN Packaging builds the release variant
- THEN Gradle assembleRelease completes without reading signing secrets
- AND the job fails if no APK is produced under `app/build/outputs/apk/release/`

### Requirement: Versioned and stable artifact names
Packaging SHALL copy the APK to a versioned name `heavy-rental-mobile-v{versionName}-build{runNumber}-{shortSha}.apk` and a stable name `heavy-rental-mobile.apk`, and SHALL upload both.

#### Scenario: Both names uploaded
- GIVEN assembleRelease produced an APK
- WHEN Packaging finishes
- THEN both the versioned and stable APK files are uploaded as artifacts
- AND both files are non-empty

### Requirement: No container registry in this change
Packaging and Publish SHALL NOT build a Docker image and SHALL NOT push to GHCR.

#### Scenario: No GHCR push
- GIVEN `workflow_dispatch` triggered the release pipeline
- WHEN Packaging and Publish complete
- THEN no `docker push` or `packages: write` permission is used

### Requirement: DAST scans the unsigned APK with MobSF
DAST SHALL run only after Packaging succeeds. It SHALL download the unsigned APK artifacts, start Mobile Security Framework (MobSF), upload the APK, write MobSF JSON/PDF under `dast-reports/`, and combine present scanner outputs into `dast-reports/combined-dast-report.pdf` (artifact `dast-combined-report-pdf`). DAST SHALL NOT start an emulator, SHALL NOT call a live Spring Boot host, and SHALL NOT run OWASP ZAP against a container.

#### Scenario: Combined DAST PDF
- GIVEN Packaging produced an APK and MobSF wrote reports
- WHEN DAST finishes
- THEN artifact `dast-combined-report-pdf` is uploaded
- AND `dast-reports/combined-dast-report.pdf` exists

#### Scenario: DAST needs Packaging
- GIVEN Packaging failed
- WHEN DAST is evaluated
- THEN DAST does not start

### Requirement: Publish creates the GitHub Release
Publish SHALL run only after Integration, Packaging, and DAST have succeeded. It SHALL create a GitHub Release on `master` (`gh release create`, tag `v{versionName}`) and attach the unsigned APKs and DAST reports. The Release caller is `workflow_dispatch` only, so this job always runs on a successful dispatch. Publish SHALL NOT push GHCR.

#### Scenario: Dispatch publishes
- GIVEN `workflow_dispatch` triggered the release pipeline
- AND DAST succeeded
- WHEN Publish runs
- THEN `gh release create` runs targeting `master`
- AND the unsigned APKs are attached
- AND no `docker push` runs
