# ADR 0005: Portal REST endpoint tests skip cleanly until scripts exist

- **Status:** Accepted
- **Date:** 2026-08-17
- **Change:** `add-portal-ci-pipeline`

## Context

The portal may not yet ship `mock:server` + `test:api` (or the documented aliases). Failing Integration CI on a missing script would block every PR.

## Decision

REST Endpoint Tests detect mock and test scripts in `package.json`. If either is missing, the job succeeds and writes a placeholder summary. When both exist, the mock binds `127.0.0.1:4010` and tests run against `MOCK_API_BASE_URL`. Release does not run this job.

## Consequences

- Branch protection can require `REST Endpoint Tests` without blocking today's tree.
- CI never points those tests at a live Academy ALB.
