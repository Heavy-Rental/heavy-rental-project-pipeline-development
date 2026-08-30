# SPDD Analysis: add-rest-cd-academy-deploy

**Companion:** [REASONS Canvas](../prompt/add-rest-cd-academy-deploy.md)

## Problem

Branch 1 can see `asg-rest` but cannot load a CI Tomcat image or refresh `.env`. As-built first-compose is infra `deploy-projects` or this CD (not infra `apply`).

## Strategy

Copy estate `guest_base` + `rest`. Pipeline `resolve-image` chooses tag or tar. Ansible over SSM, `--limit rest`. Verify is SSM `GET :8080/actuator/health` **2xx** (ALB `tg-rest` matcher `200-299`; not `GET /` 401). SM `APP_CORS_ALLOWED_ORIGINS` is for **direct** REST ALB callers; portal `/api` omits `Origin`.

## Success

`action=deploy` with a public GHCR or ECR tag updates both REST guests. `verify` is green if `:8080/actuator/health` is **2xx**.
