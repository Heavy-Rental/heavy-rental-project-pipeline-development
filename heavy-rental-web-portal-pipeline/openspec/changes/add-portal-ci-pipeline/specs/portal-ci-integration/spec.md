# Delta for portal-ci-integration

## Purpose

Highest-priority gate: fetch the React portal, install Node 22, `npm ci`, and prove install health.

On Integration CI the job id is `integration-check` and the check name is **Integration Check** (so it is not confused with Fast Feedback **Integration**). Fast Feedback and Release keep job id `integration` and name **Integration**.

## ADDED Requirements

### Requirement: Integration is first
On Integration CI, the Integration Check job SHALL run only after the caller gate succeeds and SHALL always run (it SHALL NOT be skipped with `if:`). Quality Control, Security Testing, CodeQL, and REST Endpoint Tests SHALL declare `needs: [integration-check]`. On Fast Feedback and Release, the Integration job SHALL run only after the caller gate succeeds. On Release, Quality Control and Packaging SHALL declare a dependency on Integration.

#### Scenario: Failed Integration Check blocks later CI jobs
- GIVEN Integration Check fails on Integration CI
- WHEN the workflow continues
- THEN Quality Control, Security Testing, CodeQL, and REST Endpoint Tests do not start
- AND the GitHub Flow CI Gate still runs and fails

#### Scenario: Failed Integration blocks Release packaging
- GIVEN Integration fails on Release
- WHEN the workflow continues
- THEN Quality Control, Packaging, DAST, and Publish do not start

### Requirement: Node 22
When install-health checks run, Integration SHALL install Node 22 and SHALL use that runtime for npm.

#### Scenario: Toolchain version
- GIVEN Integration has checked out the application
- AND install-health checks are not skipped
- WHEN Node is set up
- THEN the runner Node version is 22

### Requirement: npm ci on cache miss
When install-health checks run, Integration SHALL restore `node_modules` from cache keyed on `package-lock.json` when possible. On a cache miss it SHALL run `npm ci`. It SHALL fail if `package-lock.json` is missing after install checks. On Integration CI pull_request, Cache `node_modules`, `npm ci`, and install-health checks SHALL be skipped when Fast Feedback already succeeded for the PR head SHA.

#### Scenario: Lock present
- GIVEN the application contains `package-lock.json`
- AND install-health checks are not skipped
- WHEN Integration verifies install integrity
- THEN `package-lock.json` exists
- AND `node_modules` exists

#### Scenario: PR skips npm when Fast Feedback succeeded
- GIVEN Integration Check on a pull_request
- AND Fast Feedback succeeded for the PR head SHA
- WHEN Integration Check continues
- THEN Cache `node_modules`, `npm ci`, and install-health steps are skipped
- AND the job still succeeds

### Requirement: Install health
When install-health checks run, Integration SHALL print Node/npm versions, list scripts, and run `npm ls --depth=0`.

### Requirement: Fingerprint artifact
Integration SHALL upload `package.json` and `package-lock.json` as a short-lived fingerprint artifact after checkout. The upload SHALL still run when install-health checks are skipped because Fast Feedback was reused.

#### Scenario: Fingerprint uploaded
- GIVEN checkout succeeded
- WHEN Integration (or Integration Check) finishes
- THEN an artifact containing `package.json` and `package-lock.json` is uploaded

#### Scenario: Fingerprint uploaded after Fast Feedback reuse
- GIVEN Integration Check reused Fast Feedback for the PR head SHA
- WHEN Integration Check finishes
- THEN the lockfile fingerprint artifact is still uploaded
