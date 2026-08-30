# ADR 0005: Both CI callers forward Repository `REST_API_DB_*`; QC uses Environments

- **Status:** Accepted
- **Date:** 2026-08-17
- **Updated:** 2026-08-30
- **Change:** `add-rest-ci-pipeline`

## Context

Spring tests need a Postgres. Academy guests read `heavy-rental/rest` from Secrets Manager, not GitHub Actions secrets. CI still needs credentials to start a **local** Docker Postgres. Those credentials are not Academy RDS.

## Decision

- Integration CI Quality Control: `environment: integration` + `REST_API_DB_NAME` / `USER` / `PASSWORD` / `PORT`. The Integration caller **forwards** those names via an explicit `secrets:` map.
- Release Quality Control + Packaging: `environment: production` + the **same** `REST_API_DB_*` names. The Release caller **also** forwards those names via an explicit `secrets:` map (same pattern as Integration).
- Configure them as **Repository** secrets (a `uses:` job cannot read Environment secrets). Optionally also store them on Environment `integration` / `production` for isolation / protection rules.
- Neither caller uses `secrets: inherit`. Neither passes `REST_API_DB_URL`.
- `REST_API_DB_URL` is **not** a secret. QC builds `jdbc:postgresql://localhost:<PORT>/<NAME>` after the container starts.

These names are **not** the guest compose contract. Do not add `REST_API_CLOUD_DB_*` to Release or Academy.

## Consequences

- Missing `REST_API_DB_*` secrets fail QC before Postgres starts.
- Dummy local values are enough (they do not need to match Academy RDS).
- Operators must not copy CI Postgres credentials onto the EC2 or into Academy CD.
- Integration CI or Release without Repository `REST_API_DB_*` leaves the caller map empty and QC fails, even if the matching Environment has the names.
