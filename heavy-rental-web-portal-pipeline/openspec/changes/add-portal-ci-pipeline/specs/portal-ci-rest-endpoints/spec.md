# Delta for portal-ci-rest-endpoints

## Purpose

HTTP tests against a local mock API on Integration CI only. Skip cleanly until the portal defines both a mock script and a test script.

## ADDED Requirements

### Requirement: Job needs Integration
REST Endpoint Tests SHALL run only after Integration Check succeeds, in parallel with QC / Security / CodeQL.

### Requirement: Detect scripts in package.json
The job SHALL look for a mock script in this order: `mock:server`, `api:mock`, `start:mock`. It SHALL look for a test script in this order: `test:api`, `test:endpoints`, `test:rest`. It SHALL set ready only when both are present.

#### Scenario: Scripts missing skip cleanly
- GIVEN `package.json` lacks either a mock script or a test script from those lists
- WHEN REST Endpoint Tests runs
- THEN the job succeeds
- AND it does not start a mock process
- AND the step summary states the placeholder

#### Scenario: Both scripts present
- GIVEN both a mock script and a test script exist
- WHEN REST Endpoint Tests runs
- THEN the mock starts
- AND the test script runs against `MOCK_API_BASE_URL`

### Requirement: Mock bind
When ready, the mock SHALL be reached at `http://127.0.0.1:4010` (env `MOCK_API_HOST` / `MOCK_API_PORT`). The job SHALL wait on `MOCK_API_HEALTH_PATH` (default `/health`) before tests.

#### Scenario: Health wait
- GIVEN the mock is starting
- WHEN readiness is checked
- THEN the job polls `http://127.0.0.1:4010/health` (or `/`) until timeout

### Requirement: Not on Release
The Release reusable workflow SHALL NOT include a REST Endpoint Tests job.

#### Scenario: Release gate list
- GIVEN Release runs
- WHEN jobs are listed
- THEN Packaging exists
- AND REST Endpoint Tests does not
