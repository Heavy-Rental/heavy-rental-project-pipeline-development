# SPDD Analysis: add-portal-cd-academy-skeleton

**Historical (branch 1).** Compose and verify are [`add-portal-cd-academy-deploy`](add-portal-cd-academy-deploy.md). Paid/OIDC is [`add-portal-cd-paid-deploy`](add-portal-cd-paid-deploy.md). Do not treat fail-closed compose or discover-only verify as current behavior.

**Companion:** [REASONS Canvas](../prompt/add-portal-cd-academy-skeleton.md)

## Problem

No workflow in this repo can see `asg-portal` after infra apply.

## Strategy

Auth + discover only. Compose is the next branch.

## Success

`assert-lab` + `discover-targets` green after Start Lab. `deploy` fails closed.
