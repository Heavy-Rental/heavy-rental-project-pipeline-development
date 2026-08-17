# SPDD Analysis: add-portal-cd-academy-skeleton

**Companion:** [REASONS Canvas](../prompt/add-portal-cd-academy-skeleton.md)

## Problem

No workflow in this repo can see `asg-portal` after infra apply.

## Strategy

Auth + discover only. Compose is the next branch.

## Success

`assert-lab` + `discover-targets` green after Start Lab. `deploy` fails closed.
