# ADR 0001: Haystack app CD is Academy / Vocareum first

- **Status:** Accepted
- **Date:** 2026-08-17
- **Change:** `add-haystack-cd-academy-skeleton`

## Context

Haystack CD has two destinations. Academy cannot create OIDC. Paid must not receive Vocareum keys.

## Decision

The first Haystack CD workflow is **Academy only** (`haystack-cd-academy.yml`). Environment must be `academy`. Paid/OIDC is a later workflow.

## Consequences

- Same Environment secret names as infra CD.
- Pointing this workflow at `paid` fails closed.
