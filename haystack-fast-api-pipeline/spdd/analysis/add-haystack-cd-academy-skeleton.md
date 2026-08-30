# SPDD Analysis: add-haystack-cd-academy-skeleton

**Historical (branch 1).** Compose and verify are [`add-haystack-cd-academy-deploy`](add-haystack-cd-academy-deploy.md). Paid/OIDC is [`add-haystack-cd-paid-deploy`](add-haystack-cd-paid-deploy.md). Workers are [`add-haystack-cd-workers`](add-haystack-cd-workers.md). Do not treat fail-closed compose or discover-only verify as current YAML.

**Companion:** [REASONS Canvas](../prompt/add-haystack-cd-academy-skeleton.md)

## Problem

No workflow in this repo can see `asg-haystack` after infra apply.

## Strategy

Auth + discover only. Compose is the next branch.

## Success (branch 1, historical)

`assert-lab` + `discover-targets` green after Start Lab. On this branch `deploy` failed closed. Compose is delivered in [`add-haystack-cd-academy-deploy`](add-haystack-cd-academy-deploy.md); do not treat fail-closed as current YAML.
