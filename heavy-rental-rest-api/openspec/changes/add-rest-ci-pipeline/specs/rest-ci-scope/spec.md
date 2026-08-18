# Delta for rest-ci-scope

## Purpose

This family is CI and Release packaging. Academy app CD is a separate family in `deploy-pipeline/`. Infrastructure setup and operate live in the infra project.

## ADDED Requirements

### Requirement: Family does not provision infrastructure
The REST CI family SHALL NOT apply infrastructure-as-code, create cloud resources, or stand up Academy RDS, networks, or ASGs.

#### Scenario: No IaC job
- GIVEN Fast Feedback, Integration CI, or Release runs
- WHEN the workflow job list is evaluated
- THEN no job applies Terraform
- AND no job creates `asg-rest`

### Requirement: Family does not deploy
The REST CI family SHALL NOT compose onto `asg-rest` or SSH to a guest. Deployment belongs to the Academy CD family.

#### Scenario: Release stops at artifacts
- GIVEN Packaging succeeds
- WHEN the Release workflow finishes
- THEN a WAR and a gzipped image tar have been uploaded
- AND GHCR push has run only when the event is not a pull request
- AND no job runs Ansible or SSM compose

### Requirement: Family does not operate production
The REST CI family SHALL NOT monitor, scale, or run `stop` / `destroy`.

#### Scenario: No operate job
- GIVEN any pipeline in this family
- WHEN jobs complete
- THEN no job tails production logs or mutates a running ASG

### Requirement: CI database secrets are not guest config
Quality Control Docker Postgres secrets (`REST_API_DB_*` on Integration Environment `integration` and Release Environment `production`) SHALL NOT be documented or used as the guest `heavy-rental/rest` secret. Release SHALL NOT require `REST_API_CLOUD_DB_*`.

#### Scenario: Names stay separate
- GIVEN a reader of this family's specification
- WHEN they read the secret tables
- THEN guest compose is described as Academy CD + `heavy-rental/rest`
- AND `REST_API_DB_*` is described as local Docker QC only
- AND `REST_API_CLOUD_DB_*` is not listed as a required GitHub secret
