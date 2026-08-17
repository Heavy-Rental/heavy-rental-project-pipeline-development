# SPDD Analysis: add-portal-cd-academy-deploy

**Companion:** [REASONS Canvas](../prompt/add-portal-cd-academy-deploy.md)

## Problem

Branch 1 can see `asg-portal` but cannot load a CI nginx image or refresh `/api`. Compose still only exists on infra CD.

## Strategy

Copy estate `guest_base` + `portal`. Pipeline `resolve-image` chooses tag or tar. Ansible over SSM, `--limit portal`. Verify is SSM `GET /` (200–302), not `/api`.

## Success

`action=deploy` with a public GHCR or ECR tag updates both portal guests. `verify` is green if nginx answers.
