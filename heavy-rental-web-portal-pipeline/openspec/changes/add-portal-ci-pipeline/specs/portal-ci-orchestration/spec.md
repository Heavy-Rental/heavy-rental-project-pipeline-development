# Delta for portal-ci-orchestration

## Purpose

How the portal CI family is invoked. The family is Fast Feedback, Integration CI, and Release. Academy CD is a separate family. Authoring path for Integration CI is `integration_pipeline/`.

## ADDED Requirements

### Requirement: Three-pipeline family
The system SHALL provide three pipeline pairs (caller + reusable workflow): Fast Feedback, Integration CI, and Release.

#### Scenario: Fast feedback is Integration only
- GIVEN a push to a feature branch that is not `master` or `develop`
- WHEN the Fast Feedback caller runs
- THEN it invokes only the reusable fast-feedback workflow
- AND that workflow runs Integration after the caller gate
- AND it does not run Quality Control, Security Testing, CodeQL, REST Endpoint Tests, or Packaging

#### Scenario: Integration CI is the merge gate
- GIVEN a pull request targeting `develop`
- WHEN the Integration CI caller runs
- THEN it invokes the reusable integration workflow
- AND that workflow runs Integration, then Quality Control, Security Testing, CodeQL, and REST Endpoint Tests (each needing Integration)
- AND it ends with a GitHub Flow CI Gate
- AND it does not run Packaging

#### Scenario: Release adds packaging
- GIVEN a published GitHub Release, or a pull request whose head is `develop` and base is `master`
- WHEN the Release caller runs
- THEN it invokes the reusable release workflow
- AND that workflow runs Integration, Quality Control, Security Testing, CodeQL, and Packaging
- AND it does not run REST Endpoint Tests

### Requirement: Reusable workflows accept only their caller
Each reusable workflow SHALL expose only `workflow_call` and SHALL fail unless invoked by its matching caller file under `.github/workflows/`.

#### Scenario: Allowed caller
- GIVEN `integration-pipeline.yml` is invoked by `.github/workflows/portal-ci-caller.yml`
- WHEN the Assert caller job runs
- THEN the job succeeds

#### Scenario: Rejected caller
- GIVEN `integration-pipeline.yml` is invoked by any other workflow file
- WHEN the Assert caller job runs
- THEN the job fails

### Requirement: Caller triggers
Fast Feedback SHALL ignore pushes to `develop` and `master`. Integration CI SHALL own PR/push `develop` and `workflow_dispatch`. Release SHALL run on a published GitHub Release or a PR whose head is `develop` and base is `master`.

#### Scenario: Fast feedback ignores protected branches
- GIVEN a push to `develop` or `master`
- WHEN Fast Feedback is evaluated
- THEN Fast Feedback does not start from that push

### Requirement: Source resolution
Each reusable workflow SHALL check out the calling repository at the calling commit unless `app_repository` names a different repository.

#### Scenario: Same-repo caller
- GIVEN the caller is the portal repository and `app_repository` is empty
- WHEN Integration resolves the source
- THEN checkout mode is `caller`

### Requirement: Concurrency
Fast Feedback and Integration CI SHALL cancel superseded runs. Release SHALL NOT cancel an in-flight packaging run.

### Requirement: Least-privilege permissions
Only the Release caller and reusable release workflow SHALL request `packages: write`. Integration CI and Release SHALL request `security-events: write`.
