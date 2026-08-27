# Delta for portal-ci-orchestration

## Purpose

How the portal CI family is invoked: callers, reusable workflows, triggers, concurrency, permissions, and source checkout. The GitHub Flow family is Fast Feedback, Integration CI, and Release. Security Report is a scheduled/manual summary, not a merge gate. Academy CD is a separate family. Authoring path for Integration CI is `integration_pipeline/`.

## ADDED Requirements

### Requirement: Three-pipeline family
The system SHALL provide three GitHub Flow pipeline pairs (caller + reusable workflow): Fast Feedback, Integration CI, and Release. It MAY also provide a Security Report pair that is not a GitHub Flow stage.

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
- AND that workflow runs Integration Check, then Quality Control, Security Testing, CodeQL, and REST Endpoint Tests (each needing Integration Check)
- AND it ends with a GitHub Flow CI Gate
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
- AND it does not run Security Testing, CodeQL, or REST Endpoint Tests (SAST/CodeQL stay on Integration CI)

### Requirement: Reusable workflows accept only their caller
Each GitHub Flow reusable workflow SHALL expose only `workflow_call` and SHALL fail unless invoked by its matching caller file under `.github/workflows/`. The Security Report reusable SHALL fail unless invoked by a `*-security-report-caller.yml` in the same repository.

#### Scenario: Allowed caller
- GIVEN `integration-pipeline.yml` is invoked by `.github/workflows/portal-ci-caller.yml`
- WHEN the Assert caller job runs
- THEN the job succeeds

#### Scenario: Rejected caller
- GIVEN `integration-pipeline.yml` is invoked by any other workflow file
- WHEN the Assert caller job runs
- THEN the job fails

### Requirement: Caller triggers
Fast Feedback SHALL ignore pushes to `develop` and `master`. Integration CI SHALL own PR/push `develop` and `workflow_dispatch`. Release SHALL run on `workflow_dispatch` only. The Release caller SHALL NOT subscribe to `release` or `pull_request` events. Publish in a `workflow_dispatch` run is what creates the GitHub Release.

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
Fast Feedback and Integration CI SHALL check out the calling repository at the calling commit unless `app_repository` names a different repository, in which case they SHALL check out that repository at `app_ref` or the pipeline default ref (`develop`). Release SHALL check out **`master`** in both same-repo and remote modes and SHALL ignore the calling SHA and `app_ref`.

#### Scenario: Same-repo caller (Fast Feedback / Integration CI)
- GIVEN the caller is the portal repository and `app_repository` is empty
- WHEN Fast Feedback Integration or Integration Check resolves the source
- THEN checkout mode is `caller`
- AND the application is checked out at the calling `github.sha`

#### Scenario: Release always checks out master
- GIVEN a `workflow_dispatch` of the Release caller in the portal repository
- WHEN Integration resolves the source
- THEN checkout mode is `caller`
- AND the application is checked out at `master` (not the calling SHA)

#### Scenario: Remote override
- GIVEN `app_repository` is a different owner/name than the calling repository
- WHEN Fast Feedback Integration or Integration Check resolves the source
- THEN checkout mode is `remote`
- AND the named repository is checked out at `app_ref` or `develop`
- AND Release still checks out `master`

### Requirement: Concurrency
Fast Feedback and Integration CI SHALL cancel superseded runs. Release SHALL NOT cancel an in-flight packaging run.

### Requirement: Least-privilege permissions
Fast Feedback and Integration CI SHALL request `contents: read`, `pull-requests: read`, and `actions: read`. Integration CI and Release SHALL also request `security-events: write`. Integration CI SHALL also request `checks: write` (combined security PDF Checks-tab link). Only the Release caller and reusable release workflow SHALL request `packages: write` and `contents: write` (GitHub Release). Fast Feedback SHALL NOT request `packages: write` or `contents: write`. The Security Report pair SHALL request `contents: read` and `security-events: read` only.

### Requirement: Security Report is not a merge gate
The family MAY include `portal-security-report-caller.yml` plus reusable `security-report-pipeline.yml`. That pair SHALL summarize existing Code Scanning alerts into a job summary and markdown artifact. It SHALL NOT run on `pull_request` or `push`, SHALL NOT scan, and SHALL NOT be a `develop` branch-protection check.

#### Scenario: Scheduled or manual only
- GIVEN the Security Report caller
- WHEN triggers are declared
- THEN `schedule` and `workflow_dispatch` are present
- AND `pull_request` and `push` are absent

### Requirement: Fast Feedback is not invoked from Integration CI
The Integration CI caller SHALL NOT `uses:` `fast-feedback-pipeline.yml`. Fast Feedback SHALL remain the sole Integration-stage run on a feature-branch push. On `pull_request`, Integration Check SHALL reuse a successful Fast Feedback run for the PR head SHA instead of repeating `npm ci` and install-health checks.

When looking up an in-flight Fast Feedback run, Integration Check SHALL pass the pending-status jq filter inline to the `PENDING_ID` and `PENDING_URL` `jq_field` calls, matching the `SUCCESS_ID` / `SUCCESS_URL` form. It SHALL NOT assign that filter to a `PENDING_FILTER` shell variable and interpolate it on the following lines (that construction fails the wait-for-run lookup).

#### Scenario: CI caller does not call Fast Feedback
- GIVEN `portal-ci-caller.yml` is installed in the portal repository
- WHEN the Integration CI caller job is declared
- THEN it `uses:` `.github/workflows/integration-pipeline.yml`
- AND it does not `uses:` `fast-feedback-pipeline.yml`

#### Scenario: PR reuses a successful Fast Feedback run
- GIVEN a pull request targeting `develop`
- AND `portal-fast-feedback-caller.yml` has a successful run for the PR head SHA
- WHEN Integration Check runs
- THEN Cache `node_modules`, `npm ci`, and install-health checks are skipped
- AND Integration Check still succeeds so Quality Control, Security Testing, CodeQL, and REST Endpoint Tests can start

#### Scenario: PR waits for in-flight Fast Feedback
- GIVEN a pull request targeting `develop`
- AND Fast Feedback for the PR head SHA is queued or in progress
- WHEN Integration Check looks up that run
- THEN the pending-status jq filter is inlined in the `PENDING_ID` and `PENDING_URL` `jq_field` arguments (same form as `SUCCESS_ID` / `SUCCESS_URL`)
- AND it does not interpolate a `PENDING_FILTER` shell variable
- AND it waits for that run to finish
- AND if Fast Feedback succeeds, `npm ci` and install-health checks are skipped

#### Scenario: Missing or failed Fast Feedback runs locally
- GIVEN a pull request targeting `develop`
- AND Fast Feedback for the PR head SHA is missing or did not succeed
- WHEN Integration Check runs
- THEN it runs Node 22, Cache `node_modules` / `npm ci`, and install-health checks locally

#### Scenario: Non-PR Integration Check runs locally
- GIVEN a push to `develop` or `workflow_dispatch`
- WHEN Integration Check runs
- THEN it does not reuse Fast Feedback
- AND it runs Node 22, Cache `node_modules` / `npm ci`, and install-health checks locally
