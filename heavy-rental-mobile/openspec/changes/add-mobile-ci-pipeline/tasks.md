# Tasks: add-mobile-ci-pipeline

## 1. OpenSpec + OpenSPDD artifacts

- [x] 1.1 Write `openspec/config.yaml`, proposal, design, tasks, and seven capability deltas
- [x] 1.2 Write `spdd/analysis/add-mobile-ci-pipeline.md` and REASONS Canvas
- [x] 1.3 Write `specification/` index that points at both frameworks

## 2. Integration CI

- [x] 2.1 Author `integration-pipeline/integration-pipeline.yml` (reusable, caller gate, all CI jobs)
- [x] 2.2 Author `integration-pipeline/mobile-ci-caller.yml` (PR/push `develop`, `workflow_dispatch`)

## 3. Fast feedback

- [x] 3.1 Author `fast-feedback-ci-pipeline/fast-feedback-pipeline.yml` (Integration only)
- [x] 3.2 Author `fast-feedback-ci-pipeline/mobile-fast-feedback-caller.yml`

## 4. Release

- [x] 4.1 Author `release-pipeline/release-pipeline.yml` (CI gates + unsigned packaging)
- [x] 4.2 Author `release-pipeline/mobile-release-caller.yml` (published release or `develop` → `master` PR)

## 5. Verify

- [x] 5.1 Run `actionlint` on all six YAML files
- [x] 5.2 Confirm job `name:` values match branch-protection list in caller headers
- [x] 5.3 Confirm no `github.*` / `inputs.*` interpolated inside `run:` scripts
