# ADR 0001: Portal app CD is Academy / Vocareum first

- **Status:** Restored for the academy caller by [0009](0009-two-cd-actions-academy-paid.md). Paid is `portal-cd-paid-caller.yml`.
- **Date:** 2026-08-17
- **Branch:** `HR-165-implement-cd-pipeline-for-react-web-portal`

## Context

Portal CD has two destinations. Academy cannot create OIDC. Paid must not receive Vocareum keys.

## Decision

The first portal CD workflow is **Academy only** (`web-portal-cd-academy.yml`). Environment must be `academy`. Paid/OIDC is a later workflow.

## Consequences

- Same Environment secret names as infra CD.
- Pointing this workflow at `AWS_ACTUAL` fails closed (use `portal-cd-paid-caller.yml`).
