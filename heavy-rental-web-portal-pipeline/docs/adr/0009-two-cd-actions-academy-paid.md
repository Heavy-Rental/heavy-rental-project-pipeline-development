# ADR 0009: Two portal CD Actions (academy Vocareum / paid OIDC)

- **Status:** Accepted
- **Date:** 2026-08-19
- **Amends:** [0001](0001-portal-cd-academy-only.md)
- **Change:** `add-portal-cd-paid-deploy`

## Decision

1. Academy caller remains Vocareum-only.
2. Paid caller is OIDC, Environment `AWS_ACTUAL`, no Vocareum inputs.
3. Shared reusable jobs. Paid Ansible S3 is `heavy-rental-ssm-<account>-actual`.
4. No Terraform in either Action.
