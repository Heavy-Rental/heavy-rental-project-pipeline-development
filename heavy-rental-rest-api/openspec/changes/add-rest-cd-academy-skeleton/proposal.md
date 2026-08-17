# Proposal: REST CD Academy skeleton

## Why

Infra CD already creates `asg-rest` and first-composes Tomcat. REST CI already builds `tomcat:10.1-jdk21-temurin` + `ROOT.war` and pushes GHCR (non-PR) plus a Release tar. There is no REST **app CD** workflow that can authenticate to Vocareum and discover those guests without Terraform.

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

- Operators create GitHub Environment `academy` on this repo (same secret **names** as infra).
- **Not in this change:** Ansible compose, image pull, paid/OIDC, Terraform.
