# ADR 0010: Two Haystack CD Actions (academy Vocareum / paid OIDC)

- **Status:** Accepted
- **Date:** 2026-08-19
- **Amends:** [0001](0001-haystack-cd-academy-only.md)
- **Change:** `add-haystack-cd-paid-deploy`

## Decision

Academy caller Vocareum-only. Paid caller OIDC / `AWS_ACTUAL` / no Vocareum inputs. Shared jobs. Paid Ansible S3 is the SSM transfer bucket. No neo4j container. No Terraform.
