# ADR 0001: REST app CD is Academy / Vocareum first

- **Status:** Restored for the academy caller by [0008](0008-two-cd-actions-academy-paid.md). Paid is `rest-api-cd-paid-caller.yml`.
- **Date:** 2026-08-17
- **Change:** `add-rest-cd-academy-skeleton`

## Context

REST CD has two destinations. Academy cannot create OIDC. Paid must not receive Vocareum keys. CI Environments `integration` / `production` are app-build secrets, not CD.

## Decision

The first REST CD workflow is **Academy only** (`rest-api-cd-academy.yml`). Environment must be `academy`. Paid/OIDC is a later workflow.

## Consequences

- Same Environment secret names as infra CD.
- Pointing this workflow at `paid` fails closed.
