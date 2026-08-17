# ADR 0002: Vocareum keys from the event payload, masked

- **Status:** Accepted
- **Date:** 2026-08-17
- **Change:** `add-haystack-cd-academy-skeleton`

## Context

Vocareum keys change every Start Lab. `${{ inputs.aws_* }}` in `env:` dumps them in the job log.

## Decision

Read form values with `jq` from `$GITHUB_EVENT_PATH`, `::add-mask::`, then Environment `academy` fallback. Same as infra ADR 0009 and portal/REST ADR 0002.

## Consequences

- Branch 2 still needs these keys on the **runner**. They are not installed on the Haystack EC2 (`LabRole`).
