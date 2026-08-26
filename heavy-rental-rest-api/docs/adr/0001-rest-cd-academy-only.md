# ADR 0001: REST app CD is Academy / Vocareum first

- **Status:** Restored for the academy caller by [0008](0008-two-cd-actions-academy-paid.md). Paid is `rest-api-cd-paid-caller.yml`.
- **Date:** 2026-08-17
- **Change:** `add-rest-cd-academy-skeleton`

## Context

REST CD has two destinations. Academy cannot create OIDC. Paid must not receive Vocareum keys. CI Environments `integration` / `production` are app-build secrets, not CD.

## Decision

The **academy caller** (`rest-api-cd-academy-caller.yml`) is Vocareum-only. Environment must be `academy`. The reusable file `rest-api-cd-academy.yml` is **shared** by academy and paid callers (ADR 0008). Paid/OIDC is `rest-api-cd-paid-caller.yml` with Environment `AWS_ACTUAL`.

## Consequences

- Same Environment secret names as infra CD on the academy caller.
- Pointing the academy caller at a non-`academy` Environment fails closed.
- Pointing the paid caller at `academy` fails closed.
