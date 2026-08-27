# SPDD Analysis: add-mobile-ci-pipeline

**Status:** Active  
**Audience:** Implementers of the mobile GitHub Actions family  
**Companion:** [REASONS Canvas](../prompt/add-mobile-ci-pipeline.md) · [OpenSpec change](../../openspec/changes/add-mobile-ci-pipeline/proposal.md)

## Problem

`Heavy-Rental/heavy-rental-mobile` has no CI. The organization already standardized on a reusable-caller GitHub Flow family for the Spring REST API and the React portal. Copy-pasting those YAML files unchanged would install the **wrong toolchain** (Java 21 + Maven + Postgres, or Node 22 + Vite).

## Concepts

| Concept | Meaning here |
| --- | --- |
| Caller | Workflow with `on: push` / `pull_request` / `workflow_dispatch` that only `uses:` a sibling reusable file |
| Reusable pipeline | `on: workflow_call` only; `assert-caller` rejects any other file |
| Integration | Highest-priority job: checkout + toolchain + layout. Not “run instrumented tests” |
| Quality Control | Lint + JVM unit tests + debug APK. Not emulator, not Play |
| Mock Contract Tests | Node Mockoon (`mock:mockoon`) + `mock:verify` against OpenAPI. Fail if scripts missing. Not Prism, not live Spring Boot |
| Packaging | Unsigned `assembleRelease` APK. Not GHCR, not signing |
| DAST | MobSF static scan of the unsigned APK. Not ZAP against a container |
| Publish | `gh release create` on `master` from `workflow_dispatch`. Not GHCR |

## Stakeholders

- Mobile developers (need fast feedback on feature branches and green PRs into `develop`)
- Pipeline authors in this repo (must keep REST/portal conventions)
- Release managers (`workflow_dispatch` Release from `master`)

## Risks

1. **Over-building** — adding emulator, signing, or GHCR “because Android usually has them.” Forbidden in v1.
2. **Wrong Java** — inheriting Java 21 from REST API. The app is JVM 17.
3. **Secrets theatre** — inventing `environment: integration` and DB secrets the app does not use.
4. **Semgrep injection** — interpolating `${{ github.* }}` / `${{ inputs.* }}` inside `run:` scripts.
5. **Caller bypass** — a reusable file with `push:` in addition to `workflow_call`.
6. **Prism fallback** — treating Mock Contract Tests like portal skip-clean REST tests. Application ADR 003 returnNotes echo is Mockoon-only; missing scripts fail the job.

## Strategy

1. Specify behavior in OpenSpec (observable SHALL + scenarios).
2. Bind implementation in this REASONS analysis + Canvas (operations, norms, negative space).
3. Clone REST/portal **structure** (headers, gate, checkout resolver, SARIF two-pass) and replace only the toolchain and QC commands.
4. Author files under `heavy-rental-mobile/` so the Android family is self-contained.

## Success

- Six YAML files exist, `actionlint`-clean, Semgrep-safe.
- Job names match the branch-protection list in the CI caller header.
- No keystore, no emulator, no `packages: write`, no DB secrets.
- Mock Contract Tests require Mockoon; Release is dispatch-only with MobSF + GitHub Release.
