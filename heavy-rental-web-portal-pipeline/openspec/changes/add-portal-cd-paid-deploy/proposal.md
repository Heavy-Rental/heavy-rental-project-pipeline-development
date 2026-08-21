# Proposal: Portal CD paid deploy

## Why

Portal CD is Academy-only (ADR 0001). Infra paid (`aws-infra-paid.yml`, Environment `AWS_ACTUAL`) already creates `asg-portal`. Operators cannot roll a portal image onto that estate without Vocareum keys.

## What Changes

- Paid caller with OIDC, no Vocareum inputs, Environment `AWS_ACTUAL`.
- Shared reusable jobs (today’s academy YAML) accept academy | AWS_ACTUAL.
- Ansible SSM on paid uses `heavy-rental-ssm-<account>-actual`, not tfstate.
- ADR 0001 updated; ADR 0009 two CD Actions.

## Impact

- Academy caller stays Vocareum-only.
- **Not in this change:** Terraform, HTTPS, REST/Haystack groups.
