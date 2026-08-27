# Delta for rest-ci-orchestration

## Purpose

How the REST API CI family is invoked: callers, reusable workflows, triggers, concurrency, permissions, and source checkout. The GitHub Flow family is Fast Feedback, Integration CI, and Release. Security Report is a scheduled/manual summary, not a merge gate. Academy CD is a separate family.

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
- AND that workflow runs Integration Check, then Quality Control, Security Testing, and CodeQL (each needing Integration Check)
- AND it ends with a GitHub Flow CI Gate that requires all of those jobs to succeed
- AND it does not run Packaging
- AND the Integration CI caller does not `uses:` `fast-feedback-pipeline.yml`

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
Each GitHub Flow reusable workflow SHALL expose only `workflow_call` and SHALL fail unless invoked by its matching caller file under `.github/workflows/`. The Security Report reusable SHALL fail unless invoked by a `*-security-report-caller.yml` in the same repository.

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
- WHEN Fast Feedback Integration or Integration Check resolves the source
- THEN checkout mode is `caller`
- AND the application is checked out at the calling `github.sha`

#### Scenario: Release always checks out master
- GIVEN the Release caller runs in the Spring REST API repository
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
The family MAY include `rest-api-security-report-caller.yml` plus reusable `security-report-pipeline.yml`. That pair SHALL summarize existing Code Scanning alerts into a job summary and markdown artifact. It SHALL NOT run on `pull_request` or `push`, SHALL NOT scan, and SHALL NOT be a `develop` branch-protection check.

#### Scenario: Scheduled or manual only
- GIVEN the Security Report caller
- WHEN triggers are declared
- THEN `schedule` and `workflow_dispatch` are present
- AND `pull_request` and `push` are absent

### Requirement: Fast Feedback is not invoked from Integration CI
The Integration CI caller SHALL NOT `uses:` `fast-feedback-pipeline.yml`. Fast Feedback SHALL remain the sole Integration-stage run on a feature-branch push. On `pull_request`, Integration Check SHALL reuse a successful Fast Feedback run for the PR head SHA instead of repeating Maven/layout.

#### Scenario: CI caller does not call Fast Feedback
- GIVEN `rest-api-ci-caller.yml` is installed in the Spring repository
- WHEN the Integration CI caller job is declared
- THEN it `uses:` `.github/workflows/integration-pipeline.yml`
- AND it does not `uses:` `fast-feedback-pipeline.yml`

#### Scenario: PR reuses a successful Fast Feedback run
- GIVEN a pull request targeting `develop`
- AND `rest-api-fast-feedback-caller.yml` has a successful run for the PR head SHA
- WHEN Integration Check runs
- THEN Maven dependency resolve and layout checks are skipped
- AND Integration Check still succeeds so Quality Control, Security Testing, and CodeQL can start

#### Scenario: PR waits for in-flight Fast Feedback
- GIVEN a pull request targeting `develop`
- AND Fast Feedback for the PR head SHA is queued or in progress
- WHEN Integration Check looks up that run
- THEN it waits for that run to finish
- AND if Fast Feedback succeeds, Maven/layout are skipped

#### Scenario: Missing or failed Fast Feedback runs locally
- GIVEN a pull request targeting `develop`
- AND Fast Feedback for the PR head SHA is missing or did not succeed
- WHEN Integration Check runs
- THEN it runs Java 21, Maven dependency resolve, and layout checks locally

#### Scenario: Non-PR Integration Check runs locally
- GIVEN a push to `develop` or `workflow_dispatch`
- WHEN Integration Check runs
- THEN it does not reuse Fast Feedback
- AND it runs Java 21, Maven dependency resolve, and layout checks locally

### Requirement: Integration caller passes QC secrets explicitly
The Integration CI caller SHALL pass `REST_API_DB_NAME`, `REST_API_DB_USER`, `REST_API_DB_PASSWORD`, and `REST_API_DB_PORT` via an explicit `secrets:` map. It SHALL NOT set `environment:` on the `uses:` job and SHALL NOT use `secrets: inherit`. Those names SHALL be Repository secrets on the application repo (a `uses:` job cannot read Environment secrets). Quality Control SHALL still use `environment: integration`. Neither caller SHALL pass `REST_API_DB_URL`.

The Release caller SHALL NOT pass `REST_API_DB_*`, SHALL NOT set `environment:` on the `uses:` job, and SHALL NOT use `secrets: inherit`. Release Quality Control SHALL read `REST_API_DB_*` from Environment `production`.

#### Scenario: Integration caller has an explicit secrets map
- GIVEN `rest-api-ci-caller.yml` invokes the reusable integration workflow
- WHEN the job is declared
- THEN the `uses:` job has an explicit `secrets:` map for `REST_API_DB_NAME`, `REST_API_DB_USER`, `REST_API_DB_PASSWORD`, and `REST_API_DB_PORT`
- AND the `uses:` job has no `environment:` key
- AND `secrets: inherit` is absent

#### Scenario: Release caller has no secrets map
- GIVEN `rest-api-release-caller.yml` invokes the reusable release workflow
- WHEN the job is declared
- THEN the `uses:` job has no `secrets:` key
- AND the `uses:` job has no `environment:` key
