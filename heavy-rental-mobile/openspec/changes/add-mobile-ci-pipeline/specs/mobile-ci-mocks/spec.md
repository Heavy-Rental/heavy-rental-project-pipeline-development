# Delta for mobile-ci-mocks

## Purpose

Contract check of the OpenAPI-driven mock server that the Android app already ships (`npm run mock:prepare`, `mock:prism`, `mock:verify`). Analogous to the portal REST Endpoint Tests job.

## ADDED Requirements

### Requirement: Mock Contract Tests need Integration
Mock Contract Tests SHALL run only after Integration succeeds, in parallel with Quality Control, and SHALL use the same application source.

### Requirement: Detect official mock scripts
The job SHALL treat the application as ready when `package.json` defines a headless mock-server script (`mock:prism` preferred, then `mock:mockoon`) and a verify script (`mock:verify`).

#### Scenario: Scripts present
- GIVEN `package.json` contains `mock:prism` and `mock:verify`
- WHEN detection runs
- THEN the job is ready and proceeds to start Prism

#### Scenario: Scripts missing
- GIVEN either the mock-server script or `mock:verify` is absent
- WHEN detection runs
- THEN the job succeeds
- AND the step summary states that Mock Contract Tests were skipped because scripts are missing

### Requirement: Prepare, start Prism, verify
When ready, the job SHALL install Node 22 dependencies with `npm ci`, run `mock:prepare`, start the mock server in the background, wait until it accepts HTTP on the configured host/port, and run `mock:verify`.

#### Scenario: Verify passes
- GIVEN Prism is accepting HTTP on `127.0.0.1:8081`
- WHEN `npm run mock:verify` exits 0
- THEN the job succeeds
- AND the mock process is stopped afterwards

#### Scenario: Verify fails
- GIVEN Prism started
- WHEN `npm run mock:verify` exits non-zero
- THEN the job fails
- AND the mock process is still stopped

### Requirement: No live backend
Mock Contract Tests SHALL NOT start Spring Boot and SHALL NOT call a remote production or cloud API.

#### Scenario: Local mock only
- GIVEN Mock Contract Tests run
- WHEN the mock server is started
- THEN the listen address is localhost / 127.0.0.1
- AND no cloud hostname is required
