# ADR 0005: Integration QC and Release QC use GitHub `REST_API_DB_*`

- **Status:** Accepted
- **Date:** 2026-08-17
- **Updated:** 2026-08-25
- **Change:** `add-rest-ci-pipeline`

## Context

Spring tests need a Postgres. Academy guests read `heavy-rental/rest` from Secrets Manager, not GitHub Actions secrets. CI still needs credentials to start a **local** Docker Postgres. Those credentials are not Academy RDS.

## Decision

- Integration CI Quality Control: `environment: integration` + `REST_API_DB_NAME` / `USER` / `PASSWORD` / `PORT`.
- Release Quality Control + Packaging: `environment: production` + the **same** `REST_API_DB_*` names.
- `REST_API_DB_URL` is **not** a secret. QC builds `jdbc:postgresql://localhost:<PORT>/<NAME>` after the container starts.

These names are **not** the guest compose contract. Do not add `REST_API_CLOUD_DB_*` to Release or Academy.

## Consequences

- Missing `REST_API_DB_*` secrets fail QC before Postgres starts.
- Dummy local values are enough (they do not need to match Academy RDS).
- Operators must not copy CI Postgres credentials onto the EC2 or into Academy CD.
- Callers must not map `REST_API_DB_*` into the reusable workflow. A `uses:` job cannot see Environment secrets; empty values would shadow QC.
