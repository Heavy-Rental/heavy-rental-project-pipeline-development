# Heavy Rental haystack-fast-api pipelines — specification

This folder is the **human index** for the GitHub Actions family authored in `haystack-fast-api-pipeline/`.

The FastAPI / Haystack **product** specification (Call 1 / Call 2 / indexing / OpenAPI) is **not** here. It lives in the application repository:

https://github.com/Heavy-Rental/haystack-fast-api/tree/develop/openspec

Infrastructure setup (VPC, ASGs, RDS, Neo4j) is **not** specified here. It belongs to the infra project. This tree authors **CI + Release packaging**, a scheduled **Security Report**, and **Academy + paid app CD**.

## Pipeline boundaries

| Concern | Specified here? |
| --- | --- |
| Fast Feedback, Integration CI, Release packaging | Yes — CI family |
| Security Report (summarize existing Code Scanning alerts) | Yes — reporting only; not a merge gate |
| Academy and paid app CD (discover `asg-haystack` + compose) | Yes — CD family |
| Create or change infrastructure | No — infra project |
| Operate the live system (monitor, recover, `stop` / `destroy`) | No — infra project after go-live |

Operate comes after deploy. It requires knowledge of the infrastructure; it does not create it. App CD does not create the ASG.

## How to read the three frameworks

| Framework | Path | Role |
| --- | --- | --- |
| **OpenSpec** | [`../openspec/`](../openspec/) | Observable behavior: requirements and GIVEN/WHEN/THEN scenarios |
| **OpenSPDD** | [`../spdd/`](../spdd/) | Implementation contract: REASONS Canvas (how to write the YAML, what not to invent) |
| **ADR** | [`../docs/adr/`](../docs/adr/) | Why: caller gate, uv toolchain, sanitized `.env.prod` → `/app/.env` (0008), estate vs project knobs (0009), two CD Actions (0010), workers = devcontainer scripts (0011), masked Vocareum keys, reused Ansible |

Conflict order: **OpenSpec scenarios → OpenSPDD Safeguards → ADR → YAML**. If the YAML cannot satisfy a scenario without breaking a safeguard, stop and update the spec first.

## Changes

### CI family — [`../openspec/changes/add-haystack-ci-pipeline/`](../openspec/changes/add-haystack-ci-pipeline/)

As-implemented spec of Fast Feedback / Integration CI / Release YAML (PR Integration reuses Fast Feedback and waits if in-flight). Checkout is the calling repo (`github.sha`; Release always `master`). Env `DEFAULT_APP_REPOSITORY` is set to `Heavy-Rental/haystack-fast-api` but is **not interpolated**. Packaging tar is `haystack_recommender-image.tar.gz`; Publish pushes `haystack_recommender:<semver>` + `:latest` on `workflow_dispatch` only. Semgrep writes `semgrep.sarif` + `semgrep-gha.sarif` (no required `semgrep.json` / `semgrep.txt`) and a combined PDF; Code Scanning upload is best-effort. Security Report is a scheduled/manual Code Scanning summary (Monday 06:00 UTC), not a merge gate.

- Proposal: [`proposal.md`](../openspec/changes/add-haystack-ci-pipeline/proposal.md)
- Design: [`design.md`](../openspec/changes/add-haystack-ci-pipeline/design.md)
- Tasks: [`tasks.md`](../openspec/changes/add-haystack-ci-pipeline/tasks.md)
- SPDD analysis: [`../spdd/analysis/add-haystack-ci-pipeline.md`](../spdd/analysis/add-haystack-ci-pipeline.md)
- REASONS Canvas: [`../spdd/prompt/add-haystack-ci-pipeline.md`](../spdd/prompt/add-haystack-ci-pipeline.md)
- Walkthrough: [`pipelines/haystack-ci.md`](pipelines/haystack-ci.md)
- Image contract: [ADR 0008](../docs/adr/0008-haystack-ci-release-image-env-driven.md)
- Estate vs Profile knobs: [ADR 0009](../docs/adr/0009-haystack-project-profile-vs-infra-estate.md)

### CD family — skeleton then deploy

- [`../openspec/changes/add-haystack-cd-academy-skeleton/`](../openspec/changes/add-haystack-cd-academy-skeleton/)
- [`../openspec/changes/add-haystack-cd-academy-deploy/`](../openspec/changes/add-haystack-cd-academy-deploy/)
- [`../openspec/changes/add-haystack-cd-paid-deploy/`](../openspec/changes/add-haystack-cd-paid-deploy/)
- [`../openspec/changes/add-haystack-cd-workers/`](../openspec/changes/add-haystack-cd-workers/) — compose workers match estate (ADR 0011)
- SPDD: [`../spdd/analysis/add-haystack-cd-academy-skeleton.md`](../spdd/analysis/add-haystack-cd-academy-skeleton.md), [`../spdd/analysis/add-haystack-cd-academy-deploy.md`](../spdd/analysis/add-haystack-cd-academy-deploy.md), [`../spdd/analysis/add-haystack-cd-paid-deploy.md`](../spdd/analysis/add-haystack-cd-paid-deploy.md), [`../spdd/analysis/add-haystack-cd-workers.md`](../spdd/analysis/add-haystack-cd-workers.md)
- Walkthrough: [`pipelines/haystack-cd.md`](pipelines/haystack-cd.md)
- Operator: [`../docs/BOOTSTRAP.md`](../docs/BOOTSTRAP.md), [`../docs/PREPARE-HAYSTACK-REPO.md`](../docs/PREPARE-HAYSTACK-REPO.md)
- First-compose: infra `deploy-projects` (`site.yml`) or this CD (not infra `apply`)
- CD / ALB health: `GET :8000/health` **2xx** (`tg-haystack` matcher `200-299`)
- Two CD Actions: [ADR 0010](../docs/adr/0010-two-cd-actions-academy-paid.md)
- Workers: [ADR 0011](../docs/adr/0011-devcontainer-worker-sidecars.md) (`postgres:17` / `python:3.12-slim`; match estate ADR 0020)

## Workflows (implementation)

| Pipeline | Reusable | Caller (install into the app repo) |
| --- | --- | --- |
| Fast feedback | [`../fast-feedback-ci-pipeline/fast-feedback-pipeline.yml`](../fast-feedback-ci-pipeline/fast-feedback-pipeline.yml) | [`haystack-fast-feedback-caller.yml`](../fast-feedback-ci-pipeline/haystack-fast-feedback-caller.yml) |
| Integration CI | [`../integration-pipeline/integration-pipeline.yml`](../integration-pipeline/integration-pipeline.yml) | [`haystack-ci-caller.yml`](../integration-pipeline/haystack-ci-caller.yml) |
| Release | [`../release-pipeline/release-pipeline.yml`](../release-pipeline/release-pipeline.yml) | [`haystack-release-caller.yml`](../release-pipeline/haystack-release-caller.yml) |
| Security Report | [`../security-report/security-report-pipeline.yml`](../security-report/security-report-pipeline.yml) | [`haystack-security-report-caller.yml`](../security-report/haystack-security-report-caller.yml) |
| Academy CD | [`../deploy-pipeline/haystack-cd-academy.yml`](../deploy-pipeline/haystack-cd-academy.yml) | [`haystack-cd-academy-caller.yml`](../deploy-pipeline/haystack-cd-academy-caller.yml) |
| Paid CD | same reusable | [`haystack-cd-paid-caller.yml`](../deploy-pipeline/haystack-cd-paid-caller.yml) |
