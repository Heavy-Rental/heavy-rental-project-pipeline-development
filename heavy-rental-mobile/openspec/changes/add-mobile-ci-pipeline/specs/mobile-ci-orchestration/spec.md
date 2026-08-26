# Delta for mobile-ci-orchestration

## Purpose

How the mobile pipeline family is invoked: callers, reusable workflows, triggers, concurrency, permissions, and source checkout.

## ADDED Requirements

### Requirement: Three-pipeline family
The system SHALL provide three pipeline pairs (caller + reusable workflow): Fast Feedback, Integration CI, and Release.

#### Scenario: Fast feedback is Integration only
- GIVEN a push to a feature branch that is not `master` or `develop`
- WHEN the Fast Feedback caller runs
- THEN it invokes only the reusable fast-feedback workflow
- AND that workflow runs Integration after the caller gate
- AND it does not run Quality Control, Security Testing, CodeQL, Mock Contract Tests, or Packaging

#### Scenario: Integration CI is the merge gate
- GIVEN a pull request targeting `develop`
- WHEN the Integration CI caller runs
- THEN it invokes the reusable integration workflow
- AND that workflow runs Integration, then Quality Control, Security Testing, CodeQL, and Mock Contract Tests (each needing Integration)
- AND it ends with a GitHub Flow CI Gate that requires all of those jobs to succeed
- AND it does not run Packaging

#### Scenario: Release adds packaging
- GIVEN a published GitHub Release, or a pull request whose head is `develop` and base is `master`
- WHEN the Release caller runs
- THEN it invokes the reusable release workflow
- AND that workflow runs Integration, Quality Control, Security Testing, CodeQL, and Packaging
- AND Packaging needs Integration, Quality Control, Security Testing, and CodeQL
- AND Mock Contract Tests are not required for Packaging to start

### Requirement: Reusable workflows accept only their caller
Each reusable workflow SHALL expose only `workflow_call` and SHALL fail unless invoked by its matching caller file under `.github/workflows/`.

#### Scenario: Allowed caller
- GIVEN `integration-pipeline.yml` is invoked by `.github/workflows/mobile-ci-caller.yml`
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

#### Scenario: Fast feedback ignores pull requests
- GIVEN a pull request targeting `develop`
- WHEN Fast Feedback is evaluated
- THEN Fast Feedback does not start from that pull request
- AND Integration CI owns the pull request

#### Scenario: Integration CI owns develop
- GIVEN a pull request targeting `develop`, or a push to `develop`, or `workflow_dispatch`
- WHEN Integration CI is evaluated
- THEN the Integration CI caller starts

#### Scenario: Release ignores feature PRs
- GIVEN a pull request into `master` whose head branch is not `develop`
- WHEN the Release caller job is evaluated
- THEN the reusable release workflow is not invoked

### Requirement: Source resolution
Each reusable workflow SHALL check out the calling repository at the calling commit unless `app_repository` names a different repository, in which case it SHALL check out that repository at `app_ref` or the pipeline default ref.

#### Scenario: Same-repo caller
- GIVEN the caller is the mobile application repository and `app_repository` is empty
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
- GIVEN a Release run is packaging an APK
- WHEN another Release event arrives for the same ref
- THEN the in-flight run is not cancelled

### Requirement: Least-privilege permissions
Callers and reusable workflows SHALL request `contents: read`, `pull-requests: read`, and `actions: read`. Integration CI and Release SHALL also request `security-events: write`. They SHALL NOT request `packages: write` in this change. Fast Feedback and Integration CI SHALL request `actions: read` (Integration looks up Fast Feedback runs).

#### Scenario: No registry write
- GIVEN any mobile pipeline in this change
- WHEN permissions are declared
- THEN `packages: write` is absent

### Requirement: Fast Feedback is not invoked from Integration CI
The Integration CI caller SHALL NOT `uses:` `fast-feedback-pipeline.yml`. Fast Feedback SHALL remain the sole Integration-stage run on a feature-branch push. On `pull_request`, Integration SHALL reuse a successful Fast Feedback run for the PR head SHA instead of repeating Android SDK, Gradle wrapper, `:app:preBuild`, and layout checks.

When looking up an in-flight Fast Feedback run, Integration SHALL pass the pending-status jq filter inline to the `PENDING_ID` and `PENDING_URL` `jq_field` calls, matching the `SUCCESS_ID` / `SUCCESS_URL` form. It SHALL NOT assign that filter to a `PENDING_FILTER` shell variable and interpolate it on the following lines (that construction fails the wait-for-run lookup).

#### Scenario: CI caller does not call Fast Feedback
- GIVEN `mobile-ci-caller.yml` is installed in the mobile repository
- WHEN the Integration CI caller job is declared
- THEN it `uses:` `.github/workflows/integration-pipeline.yml`
- AND it does not `uses:` `fast-feedback-pipeline.yml`

#### Scenario: PR reuses a successful Fast Feedback run
- GIVEN a pull request targeting `develop`
- AND `mobile-fast-feedback-caller.yml` has a successful run for the PR head SHA
- WHEN Integration runs
- THEN Android SDK setup, Gradle wrapper, `:app:preBuild`, and layout checks are skipped
- AND Integration still succeeds so Quality Control, Security Testing, CodeQL, and Mock Contract Tests can start

#### Scenario: PR waits for in-flight Fast Feedback
- GIVEN a pull request targeting `develop`
- AND Fast Feedback for the PR head SHA is queued or in progress
- WHEN Integration looks up that run
- THEN the pending-status jq filter is inlined in the `PENDING_ID` and `PENDING_URL` `jq_field` arguments (same form as `SUCCESS_ID` / `SUCCESS_URL`)
- AND it does not interpolate a `PENDING_FILTER` shell variable
- AND it waits for that run to finish
- AND if Fast Feedback succeeds, Android SDK, Gradle wrapper, `:app:preBuild`, and layout checks are skipped

#### Scenario: Missing or failed Fast Feedback runs locally
- GIVEN a pull request targeting `develop`
- AND Fast Feedback for the PR head SHA is missing or did not succeed
- WHEN Integration runs
- THEN it runs JDK 17, Android SDK, Gradle wrapper, `:app:preBuild`, and layout checks locally

#### Scenario: Non-PR Integration runs locally
- GIVEN a push to `develop` or `workflow_dispatch`
- WHEN Integration runs
- THEN it does not reuse Fast Feedback
- AND it runs JDK 17, Android SDK, Gradle wrapper, `:app:preBuild`, and layout checks locally
