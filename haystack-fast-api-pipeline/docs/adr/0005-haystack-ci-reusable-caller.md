# ADR 0005: Haystack CI uses reusable workflows plus a sole-allowed caller

- **Status:** Accepted
- **Date:** 2026-08-17
- **Change:** `add-haystack-ci-pipeline`

## Context

REST, portal, and mobile already ship as `workflow_call` files that reject any caller other than their matching `*-caller.yml`. Haystack needs the same install story: copy the six GitHub Flow YAML files into the app repo, plus the Security Report pair (scheduled/manual only; not a merge gate).

## Decision

Each reusable file exposes only `on: workflow_call`. `assert-caller` fails unless `github.workflow_ref` ends with the matching caller filename. Fast Feedback, Integration CI, and Release are three pairs, not one mega-workflow.

Fast Feedback owns the Integration stage on feature-branch pushes. The Integration CI caller MUST NOT `uses:` `fast-feedback-pipeline.yml`. On `pull_request`, Integration looks up a successful Fast Feedback run for the PR head SHA (`gh run list` / `gh run watch`) and skips uv/layout when that run succeeded. Missing, failed, or non-PR events still run uv/layout locally. That is a lookup, not a second caller.

## Consequences

- Operators install caller + reusable side by side under `.github/workflows/`.
- A reusable file with `push` / `pull_request` / `workflow_dispatch` of its own is out of spec.
- Local `act` must skip the filename gate (`ACT=true`); GitHub-hosted runners never set that.
- Branch protection still requires the check named **Integration** (job id `integration`). Haystack has no GitHub Environment named `integration`, so the job is not renamed to Integration Check.
