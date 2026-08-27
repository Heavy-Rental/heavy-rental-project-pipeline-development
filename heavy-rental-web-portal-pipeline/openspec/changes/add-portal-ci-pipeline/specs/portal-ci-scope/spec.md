# Delta for portal-ci-scope

## Purpose

This family is CI and Release packaging. Academy and paid app CD is a separate family in `deploy-pipeline/`. Infrastructure setup and operate live in the infra project.

## ADDED Requirements

### Requirement: Family does not provision infrastructure
The portal CI family SHALL NOT apply Terraform or create `asg-portal`.

#### Scenario: No IaC job
- GIVEN Fast Feedback, Integration CI, or Release runs
- WHEN the workflow job list is evaluated
- THEN no job applies Terraform

### Requirement: Family does not deploy
The portal CI family SHALL NOT compose onto `asg-portal`. Deployment belongs to the Academy / paid CD family.

#### Scenario: Release stops at artifacts
- GIVEN Packaging and DAST succeed
- WHEN Publish finishes
- THEN a `dist/` zip and a gzipped image tar `heavy_rental_web_portal-image.tar.gz` have been uploaded
- AND GHCR push has run (dispatch-only caller) for `<semver>` and `:latest`
- AND a GitHub Release has been created on `master`
- AND no job runs Ansible

### Requirement: Family does not operate production
The portal CI family SHALL NOT run `stop` / `destroy` or monitor a live ALB.

### Requirement: Security Report does not scan or deploy
The scheduled Security Report pair SHALL summarize existing Code Scanning alerts only. It SHALL NOT run Semgrep, npm audit, Trivy, or CodeQL, SHALL NOT produce a `dist/` zip or image, and SHALL NOT compose onto `asg-portal`.

#### Scenario: Report-only
- GIVEN the Security Report workflow runs
- WHEN jobs complete
- THEN no scanner job ran
- AND no Ansible or GHCR push ran

### Requirement: No live backend
CI SHALL NOT call a live Spring or Haystack URL. REST Endpoint Tests use a local mock only.

#### Scenario: Mock only
- GIVEN REST Endpoint Tests run (scripts present)
- WHEN HTTP calls are made
- THEN they target `127.0.0.1:4010`
