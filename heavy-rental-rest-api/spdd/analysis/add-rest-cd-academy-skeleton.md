# SPDD Analysis: add-rest-cd-academy-skeleton

**Companion:** [REASONS Canvas](../prompt/add-rest-cd-academy-skeleton.md)

## Problem

No workflow in this repo can see `asg-rest` after infra apply.

## Strategy

Auth + discover only. Compose is the next branch.

## Success (branch 1, historical)

`assert-lab` + `discover-targets` green after Start Lab. On this branch `deploy` failed closed. Compose is delivered in [`add-rest-cd-academy-deploy`](add-rest-cd-academy-deploy.md); do not treat fail-closed as current YAML.
