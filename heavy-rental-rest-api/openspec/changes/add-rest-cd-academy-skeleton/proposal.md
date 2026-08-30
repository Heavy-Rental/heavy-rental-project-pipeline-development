# Proposal: REST CD Academy skeleton

**As-built:** Compose is delivered (`add-rest-cd-academy-deploy`). First-compose is infra `deploy-projects` (`site.yml`) or this app CD (not infra `apply`). GHCR is Release Publish on `workflow_dispatch` only. Keep this file as the branch-1 record.

## Why

Infra CD already creates `asg-rest`. First-compose is infra `deploy-projects` (`site.yml`) or this app CD (not infra `apply`). REST CI already builds `tomcat:10.1-jdk21-temurin` + `ROOT.war`; Publish on `workflow_dispatch` pushes GHCR plus a Release tar. There is no REST **app CD** workflow that can authenticate to Vocareum and discover those guests without Terraform.

## What Changes

- OpenSpec, OpenSPDD, ADRs 0001–0002, BOOTSTRAP.
- `deploy-pipeline/rest-api-cd-academy.yml`: `assert-lab` + `discover-targets`.
- `deploy` / `configure-only` compose fail closed (branch 2).

## Capabilities

### New Capabilities

- `rest-cd-academy-auth`
- `rest-cd-discover`
- `rest-cd-scope`

## Impact

- Operators create GitHub Environment `academy` on the Spring application repo (same secret **names** as infra).
- **Not in this change:** Ansible compose, image pull, paid/OIDC, Terraform.
