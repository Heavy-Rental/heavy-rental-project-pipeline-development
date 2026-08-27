# Delta for mobile-ci-mocks

## Purpose

Contract check of the OpenAPI-driven Mockoon server that the Android app ships (`npm run mock:mockoon`, `mock:verify`; optional `mock:prepare`). Analogous to the portal REST Endpoint Tests job, except missing scripts fail the job (they do not skip cleanly). Prism is not used in CI.

## ADDED Requirements

### Requirement: Mock Contract Tests need Integration
Mock Contract Tests SHALL run only after Integration succeeds, in parallel with Quality Control, and SHALL use the same application source. Release SHALL NOT run Mock Contract Tests.

### Requirement: Detect official mock scripts
The job SHALL treat the application as ready only when `package.json` defines `mock:mockoon` and `mock:verify`. It SHALL NOT fall back to `mock:prism` or any other mock-server script. Application ADR 003 (returnNotes echo) is Mockoon-only; CI SHALL set `MOCK_EXPECT_ECHO=1` on verify.

#### Scenario: Scripts present
- GIVEN `package.json` contains `mock:mockoon` and `mock:verify`
- WHEN detection runs
- THEN the job is ready and proceeds to start Mockoon
- AND it does not select `mock:prism`

#### Scenario: Scripts missing fail the job
- GIVEN either `mock:mockoon` or `mock:verify` is absent
- WHEN detection runs
- THEN the job fails
- AND the error states that Mock Contract Tests require `mock:mockoon` and `mock:verify`
- AND it does not skip cleanly

### Requirement: Prepare, start Mockoon, verify
When ready, the job SHALL install Node 22 dependencies with `npm ci`, run `mock:prepare` when that script exists (skip prepare when it does not), start `mock:mockoon` in the background, wait until it accepts HTTP on the configured host/port, and run `mock:verify` with `MOCK_EXPECT_ECHO=1`.

#### Scenario: Verify passes
- GIVEN Mockoon is accepting HTTP on `127.0.0.1:8081`
- WHEN `npm run mock:verify` exits 0
- THEN the job succeeds
- AND the mock process is stopped afterwards
- AND the step summary records `MOCK_EXPECT_ECHO=1`

#### Scenario: Verify fails
- GIVEN Mockoon started
- WHEN `npm run mock:verify` exits non-zero
- THEN the job fails
- AND the mock process is still stopped

#### Scenario: Prepare is optional
- GIVEN `mock:mockoon` and `mock:verify` exist
- AND `mock:prepare` is absent
- WHEN the prepare step runs
- THEN prepare is skipped
- AND Mockoon still starts

### Requirement: No live backend
Mock Contract Tests SHALL NOT start Spring Boot and SHALL NOT call a remote production or cloud API.

#### Scenario: Local mock only
- GIVEN Mock Contract Tests run
- WHEN the mock server is started
- THEN the listen address is localhost / 127.0.0.1
- AND no cloud hostname is required
