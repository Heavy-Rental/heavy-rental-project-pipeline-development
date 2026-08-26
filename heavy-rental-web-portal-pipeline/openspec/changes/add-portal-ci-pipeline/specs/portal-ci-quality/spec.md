# Delta for portal-ci-quality

## Purpose

Compile-time quality for the React SPA: ESLint and TypeScript project build. No database secrets.

## ADDED Requirements

### Requirement: Quality Control needs Integration
Quality Control SHALL run only after Integration succeeds (Integration Check on Integration CI) and SHALL check out the same application source Integration resolved.

### Requirement: ESLint then tsc
Quality Control SHALL run `npm run lint` and `npx tsc -b --pretty false`. It SHALL NOT start a mock server or run `npm run build`.

#### Scenario: Happy path
- GIVEN lint and typecheck pass
- WHEN Quality Control runs
- THEN both commands exit 0

#### Scenario: Lint failure
- GIVEN ESLint reports an error
- WHEN Quality Control runs
- THEN the job fails

### Requirement: No secrets or Environments
Quality Control SHALL NOT require GitHub Environments or repository secrets.

#### Scenario: No environment key
- GIVEN Quality Control starts
- WHEN the job is configured
- THEN it does not set `environment:`
