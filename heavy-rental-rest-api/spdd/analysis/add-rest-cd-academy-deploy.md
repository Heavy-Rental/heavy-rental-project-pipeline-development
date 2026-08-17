# SPDD Analysis: add-rest-cd-academy-deploy

**Companion:** [REASONS Canvas](../prompt/add-rest-cd-academy-deploy.md)

## Problem

Branch 1 can see `asg-rest` but cannot load a CI Tomcat image or refresh `.env`. Compose still only exists on infra CD.

## Strategy

Copy estate `guest_base` + `rest`. Pipeline `resolve-image` chooses tag or tar. Ansible over SSM, `--limit rest`. Verify is SSM `GET :8080`.

## Success

`action=deploy` with a public GHCR or ECR tag updates both REST guests. `verify` is green if Tomcat answers.
