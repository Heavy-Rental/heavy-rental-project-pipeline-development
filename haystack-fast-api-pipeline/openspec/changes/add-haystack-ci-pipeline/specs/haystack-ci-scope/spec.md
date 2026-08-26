# Delta for haystack-ci-scope

## Purpose

This family is CI and Release packaging only. Infrastructure setup, project deployment, and operate live in another project.

## ADDED Requirements

### Requirement: Family does not provision infrastructure
The haystack CI family SHALL NOT apply infrastructure-as-code, create cloud resources, or stand up databases, networks, or registries.

#### Scenario: No IaC job
- GIVEN Fast Feedback, Integration CI, or Release runs
- WHEN the workflow job list is evaluated
- THEN no job applies Terraform, Bicep, CloudFormation, or equivalent
- AND no job creates a managed database, cluster, or network

### Requirement: Family does not deploy
The haystack CI family SHALL NOT deploy a packaged artifact onto a runtime. Deployment belongs to another project that may consume Release artifacts.

#### Scenario: Release stops at artifacts
- GIVEN Packaging and DAST succeed
- WHEN Publish finishes
- THEN a wheel, sdist, and gzipped image tar have been uploaded
- AND GHCR push has run for `<semver>` and `:latest`
- AND a GitHub Release has been created on `master`
- AND no job SSHs, applies a rollout, or updates a live service

### Requirement: Family does not operate production
The haystack CI family SHALL NOT monitor, alert on, scale, or remediate a live environment. Operate belongs to another project and runs after deploy.

#### Scenario: No operate job
- GIVEN any pipeline in this family
- WHEN jobs complete
- THEN no job tails production logs, pages on-call, or mutates a running environment

### Requirement: Packaging assumes the platform already exists
Release packaging SHALL produce artifacts a later deploy project can consume and SHALL NOT require this family to have created the destination platform.

#### Scenario: Artifacts for a later deploy
- GIVEN Quality Control already passed
- WHEN Packaging finishes
- THEN versioned and stable wheel/sdist files are uploaded
- AND a non-empty image tar is uploaded
- AND the workflow does not create the host, registry, or database those artifacts will later use

### Requirement: Operate is after deploy and does not create infrastructure
Documentation and specifications for this family SHALL treat operate as a post-deploy concern that requires knowledge of the running platform and SHALL NOT describe operate as the step that provisions infrastructure.

#### Scenario: Scope text does not assign infra to operate
- GIVEN a reader of this family's specification
- WHEN they read the pipeline-boundary requirements
- THEN operate is described as after go-live
- AND infrastructure creation is described as a separate concern in another project
- AND this family is not required to implement either
