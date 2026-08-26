# Tasks: add-portal-ci-pipeline

As-implemented documentation of existing YAML. Do not edit workflow job graphs.

## 1. OpenSpec + OpenSPDD + ADR

- [x] 1.1 Write `openspec/config.yaml`, proposal, design, tasks, and eight capability deltas
- [x] 1.2 Write `spdd/analysis/add-portal-ci-pipeline.md` and REASONS Canvas
- [x] 1.3 Write CI ADRs 0004–0008 and update `docs/adr/README.md`
- [x] 1.4 Write `specification/` index and `pipelines/portal-ci.md`
- [x] 1.5 Write `docs/PREPARE-PORTAL-REPO.md`
- [x] 1.6 Vite `.env.production` sample + Release seed/scan; ADR 0008 (npm/Vite vs AWS/Spring REST)
- [x] 1.7 Release `vite build --mode api` + empty `VITE_API_TARGET` so CD `/api` reaches Spring REST
- [x] 1.8 Bake academy `VITE_STRIPE_PUBLISHABLE_KEY` at Packaging; CD overlays guest `.env`
- [x] 1.9 Record Release as `workflow_dispatch` only (Packaging → DAST → Publish GHCR + GitHub Release)

## 2. YAML

- [x] 2.1 Existing Fast Feedback / Integration / Release pairs remain the implementation
- [x] 2.2 Authoring path stays `integration_pipeline/`

## 3. Verify

- [x] 3.1 Job `name:` values in the walkthrough match YAML
- [x] 3.2 Mock host/port match `MOCK_API_*`
- [x] 3.3 Fast Feedback / Integration `DEFAULT_APP_REPOSITORY` documented as SA62-team1 act fallback; Release as Heavy-Rental
