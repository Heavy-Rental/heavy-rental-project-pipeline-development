# Delta for rest-ci-orchestration

## Purpose

How the REST API CI family is invoked: callers, reusable workflows, triggers, concurrency, permissions, and source checkout. The family is Fast Feedback, Integration CI, and Release. Academy CD is a separate family.

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

#### Scenario: Release adds packaging, DAST, and publish
- GIVEN an operator runs Actions → Release → Run workflow (`workflow_dispatch`)
- WHEN the Release caller runs
- THEN it invokes the reusable release workflow
- AND that workflow runs Integration, Quality Control, Packaging, DAST, and Publish
- AND Packaging needs Integration and Quality Control only
- AND it does not run Security Testing or CodeQL (those stay on Integration CI)
- AND DAST needs Packaging
- AND Publish needs Integration, Packaging, and DAST

### Requirement: Reusable workflows accept only their caller
Each reusable workflow SHALL expose only `workflow_call` and SHALL fail unless invoked by its matching caller file under `.github/workflows/`.

#### Scenario: Allowed caller
- GIVEN `integration-pipeline.yml` is invoked by `.github/workflows/rest-api-ci-caller.yml`
- WHEN the Assert caller job runs
- THEN the job succeeds

#### Scenario: Rejected caller
- GIVEN `integration-pipeline.yml` is invoked by any other workflow file
- WHEN the Assert caller job runs
- THEN the job fails
- AND later jobs that need Assert caller do not run

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

#### Scenario: Release is dispatch only
- GIVEN a pull request, a push, or a published GitHub Release event
- WHEN the Release caller is evaluated
- THEN the Release caller does not start from that event
- AND Release starts only from `workflow_dispatch` (it creates the GitHub Release; it must not subscribe to `on: release`)

### Requirement: Source resolution
Fast Feedback and Integration CI SHALL check out the calling repository at the calling commit unless `app_repository` names a different repository, in which case they SHALL check out that repository at `app_ref` or the pipeline default ref (`develop`). Release SHALL check out **`master`** in both same-repo and remote modes and SHALL ignore the calling SHA and `app_ref`.

#### Scenario: Same-repo caller (Fast Feedback / Integration CI)
- GIVEN the caller is the Spring REST API repository and `app_repository` is empty
- WHEN Fast Feedback or Integration CI Integration resolves the source
- THEN checkout mode is `caller`
- AND the application is checked out at the calling `github.sha`

#### Scenario: Release always checks out master
- GIVEN the Release caller runs in the Spring REST API repository
- WHEN Integration resolves the source
- THEN checkout mode is `caller`
- AND the application is checked out at `master` (not the calling SHA)

#### Scenario: Remote override
- GIVEN `app_repository` is a different owner/name than the calling repository
- WHEN Fast Feedback or Integration CI Integration resolves the source
- THEN checkout mode is `remote`
- AND the named repository is checked out at `app_ref` or `develop`
- AND Release still checks out `master`

### Requirement: Concurrency
Fast Feedback and Integration CI SHALL cancel superseded runs for the same PR or branch. Release SHALL NOT cancel an in-flight packaging run.

#### Scenario: Newer CI commit cancels the old one
- GIVEN an Integration CI run is in progress for a pull request
- WHEN a new commit is pushed to that pull request
- THEN the earlier run is cancelled

#### Scenario: Release packaging is not cancelled
- GIVEN a Release run is packaging a WAR
- WHEN another Release event arrives for the same ref
- THEN the in-flight run is not cancelled

### Requirement: Least-privilege permissions
Fast Feedback and Integration CI SHALL request `contents: read`, `pull-requests: read`, and `actions: read`. Integration CI and Release SHALL also request `security-events: write`. Only the Release caller and reusable release workflow SHALL request `packages: write` and `contents: write` (GitHub Release). Fast Feedback SHALL NOT request `packages: write` or `contents: write`.

#### Scenario: Release may write packages and create a GitHub Release
- GIVEN the Release caller or reusable release workflow
- WHEN permissions are declared
- THEN `packages: write` is present
- AND `contents: write` is present

#### Scenario: CI and fast feedback cannot write packages
- GIVEN Fast Feedback or Integration CI
- WHEN permissions are declared
- THEN `packages: write` is absent

### Requirement: Caller does not pass QC secrets
The Integration CI and Release callers SHALL NOT pass `REST_API_DB_*`, SHALL NOT set `environment:` on the `uses:` job, and SHALL NOT use `secrets: inherit`. Quality Control SHALL read `REST_API_DB_*` from its job Environment (`integration` or `production`). They SHALL NOT pass `REST_API_DB_URL`.

#### Scenario: Integration caller has no secrets map
- GIVEN `rest-api-ci-caller.yml` invokes the reusable integration workflow
- WHEN the job is declared
- THEN the `uses:` job has no `secrets:` key
- AND the `uses:` job has no `environment:` key

#### Scenario: Release caller has no secrets map
- GIVEN `rest-api-release-caller.yml` invokes the reusable release workflow
- WHEN the job is declared
- THEN the `uses:` job has no `secrets:` key
- AND the `uses:` job has no `environment:` key
