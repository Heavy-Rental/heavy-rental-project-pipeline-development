# Heavy Rental web portal pipelines — specification

This folder is the **human index** for the GitHub Actions family authored in `heavy-rental-web-portal-pipeline/`.

The React **product** specification is **not** here. It lives in the application repository.

Infrastructure setup (VPC, ASGs) is **not** specified here. It belongs to the infra project. This tree authors **CI + Release packaging**, a scheduled **Security Report**, and **Academy + paid app CD**.

The Integration CI authoring path is `integration_pipeline/` (underscore), not `integration-pipeline/`.

## Pipeline boundaries

| Concern | Specified here? |
| --- | --- |
| Fast Feedback, Integration CI, Release packaging | Yes — CI family |
| Security Report (summarize existing Code Scanning alerts) | Yes — reporting only; not a merge gate |
| Academy and paid app CD (discover `asg-portal` + compose) | Yes — CD family |
| Create or change infrastructure | No — infra project |
| Operate the live system (`stop` / `destroy`) | No — infra project after go-live |

## How to read the three frameworks

| Framework | Path | Role |
| --- | --- | --- |
| **OpenSpec** | [`../openspec/`](../openspec/) | Observable behavior: requirements and GIVEN/WHEN/THEN scenarios |
| **OpenSPDD** | [`../spdd/`](../spdd/) | Implementation contract: REASONS Canvas (how to write the YAML, what not to invent) |
| **ADR** | [`../docs/adr/`](../docs/adr/) | Why: caller gate, skip-clean REST tests, SPA image / CD-owned `/api` (0007), Vite scan file vs `--mode api` vs AWS/Spring REST (0008) |

Conflict order: **OpenSpec scenarios → OpenSPDD Safeguards → ADR → YAML**. If the YAML cannot satisfy a scenario without breaking a safeguard, stop and update the spec first.

## Changes

### CI family — [`../openspec/changes/add-portal-ci-pipeline/`](../openspec/changes/add-portal-ci-pipeline/)

As-implemented spec of Fast Feedback / Integration Check / Release YAML (PR reuses Fast Feedback and waits if in-flight; inlined pending-run jq). Checkout is the calling repo (`github.sha`; Release always `master`). Env `DEFAULT_APP_REPOSITORY` is set to `Heavy-Rental/heavy-rental-react-web-portal` but is **not interpolated**. Release is `workflow_dispatch` only (Packaging → DAST → Publish GHCR + GitHub Release). Security Report is a scheduled/manual Code Scanning summary (Monday 08:00 UTC), not a merge gate.

- Proposal: [`proposal.md`](../openspec/changes/add-portal-ci-pipeline/proposal.md)
- Design: [`design.md`](../openspec/changes/add-portal-ci-pipeline/design.md)
- Tasks: [`tasks.md`](../openspec/changes/add-portal-ci-pipeline/tasks.md)
- SPDD analysis: [`../spdd/analysis/add-portal-ci-pipeline.md`](../spdd/analysis/add-portal-ci-pipeline.md)
- REASONS Canvas: [`../spdd/prompt/add-portal-ci-pipeline.md`](../spdd/prompt/add-portal-ci-pipeline.md)
- Walkthrough: [`pipelines/portal-ci.md`](pipelines/portal-ci.md)
- Image contract: [ADR 0007](../docs/adr/0007-portal-ci-release-image-cloud-ready.md)
- Vite profile vs AWS: [ADR 0008](../docs/adr/0008-portal-vite-profile-vs-infra-estate.md)

### CD family — skeleton then deploy

- [`../openspec/changes/add-portal-cd-academy-skeleton/`](../openspec/changes/add-portal-cd-academy-skeleton/)
- [`../openspec/changes/add-portal-cd-academy-deploy/`](../openspec/changes/add-portal-cd-academy-deploy/)
- [`../openspec/changes/add-portal-cd-paid-deploy/`](../openspec/changes/add-portal-cd-paid-deploy/)
- SPDD: [`../spdd/analysis/add-portal-cd-academy-skeleton.md`](../spdd/analysis/add-portal-cd-academy-skeleton.md), [`../spdd/analysis/add-portal-cd-academy-deploy.md`](../spdd/analysis/add-portal-cd-academy-deploy.md), [`../spdd/analysis/add-portal-cd-paid-deploy.md`](../spdd/analysis/add-portal-cd-paid-deploy.md)
- Walkthrough: [`pipelines/portal-cd.md`](pipelines/portal-cd.md) (`configure-only` three stores on `academy` or `AWS_ACTUAL`)
- Operator: [`../docs/BOOTSTRAP.md`](../docs/BOOTSTRAP.md), [`../docs/PREPARE-PORTAL-REPO.md`](../docs/PREPARE-PORTAL-REPO.md)
- First-compose: infra `deploy-projects` (`site.yml`) or this CD (not infra `apply`)
- CD / ALB health: `GET :80/` **200 / 301 / 302** (ALB `tg-portal` matcher `200-399`)
- Two CD Actions: [ADR 0009](../docs/adr/0009-two-cd-actions-academy-paid.md)

## Workflows (implementation)

| Pipeline | Reusable | Caller (install into the app repo) |
| --- | --- | --- |
| Fast feedback | [`../fast-feedback-ci-pipeline/fast-feedback-pipeline.yml`](../fast-feedback-ci-pipeline/fast-feedback-pipeline.yml) | [`portal-fast-feedback-caller.yml`](../fast-feedback-ci-pipeline/portal-fast-feedback-caller.yml) |
| Integration CI | [`../integration_pipeline/integration-pipeline.yml`](../integration_pipeline/integration-pipeline.yml) | [`portal-ci-caller.yml`](../integration_pipeline/portal-ci-caller.yml) |
| Release | [`../release-pipeline/release-pipeline.yml`](../release-pipeline/release-pipeline.yml) | [`portal-release-caller.yml`](../release-pipeline/portal-release-caller.yml) |
| Security Report | [`../security-report/security-report-pipeline.yml`](../security-report/security-report-pipeline.yml) | [`portal-security-report-caller.yml`](../security-report/portal-security-report-caller.yml) |
| Academy CD | [`../deploy-pipeline/web-portal-cd-academy.yml`](../deploy-pipeline/web-portal-cd-academy.yml) | [`portal-cd-academy-caller.yml`](../deploy-pipeline/portal-cd-academy-caller.yml) |
| Paid CD | same reusable | [`portal-cd-paid-caller.yml`](../deploy-pipeline/portal-cd-paid-caller.yml) |
