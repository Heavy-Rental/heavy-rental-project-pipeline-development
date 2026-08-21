# ADR 0008: Two REST CD Actions (academy Vocareum / paid OIDC)

- **Status:** Accepted
- **Date:** 2026-08-19
- **Amends:** [0001](0001-rest-cd-academy-only.md)
- **Change:** `add-rest-cd-paid-deploy`

## Decision

Academy caller Vocareum-only. Paid caller OIDC / `AWS_ACTUAL` / no Vocareum inputs. Shared jobs. Paid Ansible S3 is the SSM transfer bucket. No Terraform.
