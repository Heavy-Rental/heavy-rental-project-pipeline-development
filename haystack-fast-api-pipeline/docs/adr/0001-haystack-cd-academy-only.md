# ADR 0001: Haystack app CD is Academy / Vocareum first

- **Status:** Restored for the academy caller by [0010](0010-two-cd-actions-academy-paid.md). Paid is `haystack-cd-paid-caller.yml`.
- **Date:** 2026-08-17
- **Change:** `add-haystack-cd-academy-skeleton`

## Context

Haystack CD has two destinations. Academy cannot create OIDC. Paid must not receive Vocareum keys.

## Decision

The **academy caller** (`haystack-cd-academy-caller.yml`) is Vocareum-only. Environment must be `academy`. The reusable file `haystack-cd-academy.yml` is **shared** by academy and paid callers (ADR 0010). Paid/OIDC is `haystack-cd-paid-caller.yml` with Environment `AWS_ACTUAL`.

## Consequences

- Same Environment secret names as infra CD on the academy caller.
- Pointing the academy caller at a non-`academy` Environment fails closed.
- Pointing the paid caller at `academy` fails closed.
