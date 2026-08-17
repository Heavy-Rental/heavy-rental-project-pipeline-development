# ADR 0001: Portal app CD is Academy / Vocareum first

- **Status:** Accepted
- **Date:** 2026-08-17
- **Branch:** `HR-165-implement-cd-pipeline-for-react-web-portal`

## Context

Portal CD has two destinations. Academy cannot create OIDC. Paid must not receive Vocareum keys.

## Decision

The first portal CD workflow is **Academy only** (`web-portal-cd-academy.yml`). Environment must be `academy`. Paid/OIDC is a later workflow.

## Consequences

- Same Environment secret names as infra CD.
- Pointing this workflow at `paid` fails closed.
