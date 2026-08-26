# Delta for haystack-ci-orchestration

## Purpose

How the haystack-fast-api pipeline family is invoked: callers, reusable workflows, triggers, concurrency, permissions, and source checkout. The family is Fast Feedback, Integration CI, and Release only. Infrastructure, deploy, and operate are specified in another project.

## ADDED Requirements

### Requirement: Three-pipeline family
The system SHALL provide three pipeline pairs (caller + reusable workflow): Fast Feedback, Integration CI, and Release.

#### Scenario: Fast feedback is Integration only
- GIVEN a push to a feature branch that is not `master` or `develop`
- WHEN the Fast Feedback caller runs
- THEN it invokes only the reusable fast-feedback workflow
- AND that workflow runs Integration after the caller gate
- AND it does not run Quality Control, Security Testing, CodeQL, or Packaging

#### Scenario: Integration CI is the merge gate
- GIVEN a pull request targeting `develop`
- WHEN the Integration CI caller runs
- THEN it invokes the reusable integration workflow
- AND that workflow runs Integration, then Quality Control, Security Testing, and CodeQL (each needing Integration)
- AND it ends with a GitHub Flow CI Gate that requires all of those jobs to succeed
- AND it does not run Packaging

#### Scenario: Release adds packaging, DAST, and Publish
- GIVEN a `workflow_dispatch` of the Release caller
- WHEN the Release caller runs
- THEN it invokes the reusable release workflow
- AND that workflow runs Integration, Quality Control, Packaging, DAST, and Publish
- AND Packaging needs Integration and Quality Control
- AND DAST needs Packaging
- AND Publish needs Integration, Packaging, and DAST
- AND it does not run Security Testing or CodeQL (those stay on Integration CI)

### Requirement: Reusable workflows accept only their caller
Each reusable workflow SHALL expose only `workflow_call` and SHALL fail unless invoked by its matching caller file under `.github/workflows/`.

#### Scenario: Allowed caller
- GIVEN `integration-pipeline.yml` is invoked by `.github/workflows/haystack-ci-caller.yml`
- WHEN the Assert caller job runs
- THEN the job succeeds

#### Scenario: Rejected caller
- GIVEN `integration-pipeline.yml` is invoked by any other workflow file
- WHEN the Assert caller job runs
- THEN the job fails
- AND later jobs that need Assert caller do not run

#### Scenario: nektos/act has no workflow_ref
- GIVEN the job is running under nektos/act (`ACT` is `true`)
- AND `github.workflow_ref` is empty
- WHEN the Assert caller job runs
- THEN the filename gate is skipped
- AND the job succeeds
- AND the same empty `workflow_ref` on GitHub-hosted runners (where `ACT` is unset) still fails

### Requirement: Caller triggers
Each caller SHALL use the GitHub Flow triggers defined for its pipeline and SHALL NOT subscribe to the other pipelines' events.

#### Scenario: Fast feedback ignores protected branches
- GIVEN a push to `develop` or `master`
- WHEN Fast Feedback is evaluated
- THEN Fast Feedback does not start from that push

#### Scenario: Integration CI owns develop
- GIVEN a pull request targeting `develop`, or a push to `develop`, or `workflow_dispatch`
- WHEN Integration CI is evaluated
- THEN the Integration CI caller starts

#### Scenario: Release is manual dispatch only
- GIVEN `workflow_dispatch` on the Release caller
- WHEN the caller is evaluated
- THEN it invokes the reusable release workflow

#### Scenario: Release ignores GitHub Release publish and PRs
- GIVEN a published GitHub Release, or a pull request whose head is `develop` and base is `master`
- WHEN Release is evaluated
- THEN the Release caller does not start
- AND Publish in a `workflow_dispatch` run is what creates the GitHub Release

### Requirement: Source resolution
Each reusable workflow SHALL check out the calling repository at the calling commit unless `app_repository` names a different repository, in which case it SHALL check out that repository at `app_ref` or the pipeline default ref.

#### Scenario: Same-repo caller
- GIVEN the caller is the haystack-fast-api repository and `app_repository` is empty
- WHEN Integration resolves the source
- THEN checkout mode is `caller`
- AND the application is checked out at the calling `github.sha`

#### Scenario: Remote override
- GIVEN `app_repository` is a different owner/name than the calling repository
- WHEN Integration resolves the source
- THEN checkout mode is `remote`
- AND the named repository is checked out at `app_ref` or the default ref (`develop` for fast feedback and CI, `master` for release)

### Requirement: Concurrency
Fast Feedback and Integration CI SHALL cancel superseded runs for the same PR or branch. Release SHALL NOT cancel an in-flight packaging run.

#### Scenario: Newer CI commit cancels the old one
- GIVEN an Integration CI run is in progress for a pull request
- WHEN a new commit is pushed to that pull request
- THEN the earlier run is cancelled

#### Scenario: Release packaging is not cancelled
- GIVEN a Release run is packaging a wheel
- WHEN another Release event arrives for the same ref
- THEN the in-flight run is not cancelled

### Requirement: Least-privilege permissions
Callers and reusable workflows SHALL request `contents: read`, `pull-requests: read`, and `actions: read`. Integration CI and Release SHALL also request `security-events: write`. Only the Release caller and reusable release workflow SHALL request `packages: write`. Fast Feedback and Integration CI SHALL NOT request `packages: write`.

#### Scenario: Release may write packages
- GIVEN the Release caller or reusable release workflow
- WHEN permissions are declared
- THEN `packages: write` is present

#### Scenario: CI and fast feedback cannot write packages
- GIVEN Fast Feedback or Integration CI
- WHEN permissions are declared
- THEN `packages: write` is absent

### Requirement: No mock-contract job
The family SHALL NOT include a Mock Contract Tests / Prism job. HTTP coverage is pytest + FastAPI `TestClient` in Quality Control.

#### Scenario: Gate list has no mocks
- GIVEN Integration CI finishes
- WHEN the GitHub Flow CI Gate aggregates results
- THEN it requires Integration, Quality Control, Security Testing, and CodeQL
- AND it does not require a Mock Contract Tests job
