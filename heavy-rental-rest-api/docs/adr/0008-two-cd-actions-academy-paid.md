# ADR 0008: Two REST CD Actions (academy Vocareum / paid OIDC)

- **Status:** Accepted
- **Date:** 2026-08-19
- **Updated:** 2026-08-26
- **Amends:** [0001](0001-rest-cd-academy-only.md)
- **Change:** `add-rest-cd-paid-deploy`

## Context

Academy cannot create GitHub OIDC. Paid must not receive Vocareum keys. One reusable job graph should serve both destinations so compose, image resolve, and verify do not fork.

## Decision

Academy caller is Vocareum-only (`rest-api-cd-academy-caller.yml`, Environment `academy`). Paid caller is OIDC / Environment `AWS_ACTUAL` / no Vocareum inputs (`rest-api-cd-paid-caller.yml`). Both `uses:` `rest-api-cd-academy.yml`. Paid Ansible S3 is `heavy-rental-ssm-<account>-actual`. Academy keeps the tfstate bucket for SSM transfer. No Terraform.

The paid caller may use `secrets: inherit` so Environment `AWS_ACTUAL` is visible to the reusable jobs. The academy caller must not inherit (Vocareum keys come from the event payload or explicit inputs). The CI-family “no `secrets: inherit`” rule does not apply here.

The academy caller still declares `id-token: write` so GitHub will let it `uses:` the shared reusable (`rest-api-cd-academy.yml`, also called by paid OIDC). Academy authenticates with Vocareum keys, not GitHub OIDC.

## Consequences

- Operators run **REST API CD (Academy)** or **REST API CD (paid)**, not one Action with a profile dropdown.
- Shared jobs accept `academy` or `AWS_ACTUAL`.
- Vocareum form keys on paid fail closed.
- Academy `id-token: write` is workflow-call plumbing, not a switch to OIDC.
