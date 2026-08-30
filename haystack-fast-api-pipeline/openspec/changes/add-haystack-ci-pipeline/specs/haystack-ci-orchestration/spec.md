# Delta for haystack-ci-orchestration

## Purpose

How the haystack-fast-api pipeline family is invoked: callers, reusable workflows, triggers, concurrency, permissions, and source checkout. The GitHub Flow family is Fast Feedback, Integration CI, and Release. Security Report is a scheduled/manual summary, not a merge gate. Academy CD is a separate family.

## ADDED Requirements

### Requirement: Three-pipeline family
The system SHALL provide three GitHub Flow pipeline pairs (caller + reusable workflow): Fast Feedback, Integration CI, and Release. It MAY also provide a Security Report pair that is not a GitHub Flow stage.

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
- AND the Integration CI caller does not `uses:` `fast-feedback-pipeline.yml`

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
Each GitHub Flow reusable workflow SHALL expose only `workflow_call` and SHALL fail unless invoked by its matching caller file under `.github/workflows/`. The Security Report reusable SHALL fail unless invoked by `haystack-security-report-caller.yml` in the same repository.

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
Fast Feedback and Integration CI SHALL check out the calling repository at the calling commit unless `app_repository` names a different repository, in which case they SHALL check out that repository at `app_ref` or the pipeline default ref. Release SHALL always check out **`master`** (same-repo or remote) and SHALL ignore `app_ref`. Env `DEFAULT_APP_REPOSITORY` MAY be set for documentation; it SHALL NOT be interpolated as the checkout default.

#### Scenario: Same-repo caller
- GIVEN the caller is the haystack-fast-api repository and `app_repository` is empty
- WHEN Integration resolves the source
- THEN checkout mode is `caller`
- AND the application is checked out at the calling `github.sha`

#### Scenario: Remote override
- GIVEN `app_repository` is a different owner/name than the calling repository
- WHEN Integration resolves the source
- THEN checkout mode is `remote`
- AND the named repository is checked out at `app_ref` or the default ref (`develop` for fast feedback and CI)

#### Scenario: Release always checks out master
- GIVEN the Release caller
- WHEN source is resolved
- THEN the application is checked out at `master`
- AND `app_ref` is ignored

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
Fast Feedback and Integration CI SHALL request `contents: read`, `pull-requests: read`, and `actions: read`. Integration CI and Release SHALL also request `security-events: write`. Integration CI SHALL also request `checks: write` (combined security PDF Checks-tab link). Only the Release caller and reusable release workflow SHALL request `packages: write` and `contents: write` (GitHub Release). Fast Feedback SHALL NOT request `packages: write` or `contents: write`. The Security Report pair SHALL request `contents: read` and `security-events: read` only.

#### Scenario: Release may write packages and create a GitHub Release
- GIVEN the Release caller or reusable release workflow
- WHEN permissions are declared
- THEN `packages: write` is present
- AND `contents: write` is present

#### Scenario: CI and fast feedback cannot write packages
- GIVEN Fast Feedback or Integration CI
- WHEN permissions are declared
- THEN `packages: write` is absent

#### Scenario: Integration CI may write Checks
- GIVEN the Integration CI caller or reusable integration workflow
- WHEN permissions are declared
- THEN `checks: write` is present

### Requirement: Security Report is not a merge gate
The family MAY include `haystack-security-report-caller.yml` plus reusable `security-report-pipeline.yml`. That pair SHALL summarize existing Code Scanning alerts into a job summary and markdown artifact. It SHALL NOT run on `pull_request` or `push`, SHALL NOT scan, and SHALL NOT be a `develop` branch-protection check.

#### Scenario: Scheduled or manual only
- GIVEN the Security Report caller
- WHEN triggers are declared
- THEN `schedule` and `workflow_dispatch` are present
- AND `pull_request` and `push` are absent

### Requirement: Fast Feedback is not invoked from Integration CI
The Integration CI caller SHALL NOT `uses:` `fast-feedback-pipeline.yml`. Fast Feedback SHALL remain the sole Integration-stage run on a feature-branch push. On `pull_request`, Integration SHALL reuse a successful Fast Feedback run for the PR head SHA instead of repeating uv/layout.

#### Scenario: CI caller does not call Fast Feedback
- GIVEN `haystack-ci-caller.yml` is evaluated
- WHEN it starts jobs
- THEN it does not `uses:` `fast-feedback-pipeline.yml`

#### Scenario: PR reuses a successful Fast Feedback run
- GIVEN Integration on a `pull_request`
- AND Fast Feedback succeeded for the PR head SHA
- WHEN Integration continues
- THEN uv lock/sync and Haystack/layout smoke are skipped
- AND the Integration job still succeeds

#### Scenario: PR waits for in-flight Fast Feedback
- GIVEN Integration on a `pull_request`
- AND Fast Feedback for the PR head SHA is queued or in progress
- WHEN Integration looks up that run
- THEN it waits for the run to finish
- AND if Fast Feedback succeeds, uv/layout are skipped

#### Scenario: Missing or failed Fast Feedback runs locally
- GIVEN Integration on a `pull_request`
- AND Fast Feedback for the PR head SHA is missing or did not succeed
- WHEN Integration continues
- THEN uv/layout run locally

#### Scenario: Non-PR events do not reuse Fast Feedback
- GIVEN Integration on `push` to `develop` or `workflow_dispatch`
- WHEN Integration continues
- THEN it does not reuse Fast Feedback

### Requirement: No mock-contract job
The family SHALL NOT include a Mock Contract Tests / Prism job. HTTP coverage is pytest + FastAPI `TestClient` in Quality Control.

#### Scenario: Gate list has no mocks
- GIVEN Integration CI finishes
- WHEN the GitHub Flow CI Gate aggregates results
- THEN it requires Integration, Quality Control, Security Testing, and CodeQL
- AND it does not require a Mock Contract Tests job
