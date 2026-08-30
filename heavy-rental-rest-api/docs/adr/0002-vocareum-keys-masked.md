# ADR 0002: Vocareum keys from the event payload, masked

- **Status:** Accepted
- **Date:** 2026-08-17
- **Change:** `add-rest-cd-academy-skeleton`

## Context

Vocareum keys change every Start Lab. `${{ inputs.aws_* }}` in `env:` dumps them in the job log.

## Decision

Read form values with `jq` from `$GITHUB_EVENT_PATH`, `::add-mask::`, then Environment `academy` fallback. Same as infra ADR 0009 and portal ADR 0002. The Run Inputs page may still show the strings (GitHub has no secret-typed input).

## Consequences

- Academy CD still needs these keys on the **runner** (form or Environment) to call AWS. They are not installed on the REST EC2 (`LabRole`).
