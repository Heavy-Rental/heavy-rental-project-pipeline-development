# ADR 0005: Integration QC and Release QC use different secret families

- **Status:** Accepted
- **Date:** 2026-08-17
- **Change:** `add-rest-ci-pipeline`

## Context

Spring tests need a Postgres. Academy guests read `heavy-rental/rest` from Secrets Manager, not GitHub Actions secrets. CI still needs credentials to start a **local** Docker Postgres.

## Decision

- Integration CI Quality Control: `environment: integration` + `REST_API_DB_NAME` / `USER` / `PASSWORD` / `PORT`. JDBC URL is built as localhost after the container starts.
- Release Quality Control + Packaging: `environment: production` + `REST_API_CLOUD_DB_*`. Tests still hit localhost Docker. Packaging records a cloud JDBC URL **without password** for later deploy consumers.

These names are **not** the guest compose contract.

## Consequences

- Missing secrets fail QC before Postgres starts.
- Operators must not copy `REST_API_CLOUD_DB_*` onto the EC2 or into Academy CD.
