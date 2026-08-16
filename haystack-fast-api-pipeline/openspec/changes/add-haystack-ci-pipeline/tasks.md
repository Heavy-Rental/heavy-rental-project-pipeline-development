# Tasks: add-haystack-ci-pipeline

## 1. OpenSpec + OpenSPDD artifacts

- [x] 1.1 Write `openspec/config.yaml`, proposal, design, tasks, and six capability deltas
- [x] 1.2 Write `spdd/analysis/add-haystack-ci-pipeline.md` and REASONS Canvas
- [x] 1.3 Write `specification/` index that points at both frameworks

## 2. Integration CI

- [x] 2.1 Author `integration-pipeline/integration-pipeline.yml` (reusable, caller gate, Python/Haystack jobs)
- [x] 2.2 Author `integration-pipeline/haystack-ci-caller.yml` (PR/push `develop`, `workflow_dispatch`)

## 3. Fast feedback

- [x] 3.1 Author `fast-feedback-ci-pipeline/fast-feedback-pipeline.yml` (Integration only)
- [x] 3.2 Author `fast-feedback-ci-pipeline/haystack-fast-feedback-caller.yml`

## 4. Release

- [x] 4.1 Author `release-pipeline/release-pipeline.yml` (CI gates + `uv build`)
- [x] 4.2 Author `release-pipeline/haystack-release-caller.yml` (published release or `develop` → `master` PR)

## 5. Verify

- [x] 5.1 Run `actionlint` on all six YAML files
- [x] 5.2 Confirm job `name:` values match branch-protection list in caller headers
- [x] 5.3 Confirm no `github.*` / `inputs.*` interpolated inside `run:` scripts
- [x] 5.4 Confirm toolchain is Python/uv/Ruff/pytest/Haystack (no Java, Gradle, Node, or Postgres)

## 6. Documentation rewrite (renamed tree + CI scope)

- [x] 6.1 Rewrite `README.md`, `specification/README.md`, and `specification/pipelines/haystack-ci.md` for `haystack-fast-api-pipeline/`
- [x] 6.2 Document CI vs infrastructure vs deploy vs operate (those last three are another project)
- [x] 6.3 Add `haystack-ci-scope` capability and update proposal, design, OpenSPDD
- [x] 6.4 Point YAML header `actionlint` / `act` paths at `haystack-fast-api-pipeline/`
- [x] 6.5 Fix `act/run-act.sh` `HAYSTACK` root and `act/README.md` commands
