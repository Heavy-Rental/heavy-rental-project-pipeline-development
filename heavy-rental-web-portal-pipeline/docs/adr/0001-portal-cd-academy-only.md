# ADR 0001: Portal app CD is Academy / Vocareum first

- **Status:** Restored for the academy caller by [0009](0009-two-cd-actions-academy-paid.md). Paid is `portal-cd-paid-caller.yml`.
- **Date:** 2026-08-17
- **Branch:** `HR-165-implement-cd-pipeline-for-react-web-portal`

## Context

Portal CD has two destinations. Academy cannot create OIDC. Paid must not receive Vocareum keys.

## Decision

The **academy caller** (`portal-cd-academy-caller.yml`) is Vocareum-only. Environment must be `academy`. The reusable file `web-portal-cd-academy.yml` is **shared** by academy and paid callers (ADR 0009). Paid/OIDC is `portal-cd-paid-caller.yml` with Environment `AWS_ACTUAL`.

## Consequences

- Same Environment secret names as infra CD on the academy caller.
- Pointing the academy caller at a non-`academy` Environment fails closed.
- Pointing the paid caller at `academy` fails closed.
