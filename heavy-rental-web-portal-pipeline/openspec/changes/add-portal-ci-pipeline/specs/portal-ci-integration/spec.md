# Delta for portal-ci-integration

## Purpose

Highest-priority gate: fetch the React portal, install Node 22, `npm ci`, and prove install health.

## ADDED Requirements

### Requirement: Integration is first
The Integration job SHALL run only after the caller gate succeeds. Later jobs SHALL declare a dependency on Integration.

#### Scenario: Failed Integration blocks later jobs
- GIVEN Integration fails
- WHEN the workflow continues
- THEN Quality Control, Security Testing, CodeQL, REST Endpoint Tests, and Packaging do not start

### Requirement: Node 22
Integration SHALL install Node 22 and SHALL use that runtime for npm.

#### Scenario: Toolchain version
- GIVEN Integration has checked out the application
- WHEN Node is set up
- THEN the runner Node version is 22

### Requirement: npm ci on cache miss
Integration SHALL restore `node_modules` from cache keyed on `package-lock.json` when possible. On a cache miss it SHALL run `npm ci`. It SHALL fail if `package-lock.json` is missing after install checks.

#### Scenario: Lock present
- GIVEN the application contains `package-lock.json`
- WHEN Integration verifies install integrity
- THEN `package-lock.json` exists
- AND `node_modules` exists

### Requirement: Install health
Integration SHALL print Node/npm versions, list scripts, and run `npm ls --depth=0`.

### Requirement: Fingerprint artifact
Integration SHALL upload `package.json` and `package-lock.json` as a short-lived fingerprint artifact.
