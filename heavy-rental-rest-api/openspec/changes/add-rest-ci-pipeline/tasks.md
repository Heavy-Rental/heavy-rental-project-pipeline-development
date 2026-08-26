# Tasks: add-rest-ci-pipeline

As-implemented documentation of existing YAML. Do not edit workflow job graphs.

## 1. OpenSpec + OpenSPDD + ADR

- [x] 1.1 Write `openspec/config.yaml`, proposal, design, tasks, and seven capability deltas
- [x] 1.2 Write `spdd/analysis/add-rest-ci-pipeline.md` and REASONS Canvas
- [x] 1.3 Write CI ADRs 0004–0007 and update `docs/adr/README.md`
- [x] 1.4 Write `specification/` index and `pipelines/rest-ci.md` (dispatch-only Release; DAST + Publish; SAST on Integration CI only)

## 2. YAML

- [x] 2.1 Existing Fast Feedback / Integration / Release pairs remain the implementation
- [x] 2.2 No new jobs in this change

## 3. Verify

- [x] 3.1 Job `name:` values in the walkthrough match YAML
- [x] 3.2 Secret names match caller `secrets:` maps
- [x] 3.3 `DEFAULT_APP_REPOSITORY` documented as SA62-team1 act fallback on Fast Feedback / Integration CI; Release uses Heavy-Rental
