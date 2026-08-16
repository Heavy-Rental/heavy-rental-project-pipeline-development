# Delta for mobile-ci-release

## Purpose

Release packaging produces unsigned, versioned Android APK artifacts after the quality and security gates pass.

## ADDED Requirements

### Requirement: Packaging waits for gates
Packaging SHALL run only after Integration, Quality Control, Security Testing, and CodeQL have succeeded.

#### Scenario: Security red blocks packaging
- GIVEN Security Testing failed
- WHEN Packaging is evaluated
- THEN Packaging does not start

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
Packaging SHALL NOT build a Docker image and SHALL NOT push to GHCR.

#### Scenario: No GHCR push
- GIVEN a published GitHub Release triggered the release pipeline
- WHEN Packaging completes
- THEN no `docker push` or `packages: write` permission is used
