# Heavy Rental haystack-fast-api pipelines — specification

This folder is the **human index** for the GitHub Actions family authored in `haystack-fast-api-pipeline/`.

The FastAPI / Haystack **product** specification (Call 1 / Call 2 / indexing / OpenAPI) is **not** here. It lives in the application repository:

https://github.com/Heavy-Rental/haystack-fast-api/tree/develop/openspec

Infrastructure setup (VPC, ASGs, RDS, Neo4j) is **not** specified here. It belongs to the infra project. This tree authors **CI + Release packaging** and **Academy app CD**.

## Pipeline boundaries

| Concern | Specified here? |
| --- | --- |
| Fast Feedback, Integration CI, Release packaging | Yes — CI family |
| Academy app CD (discover `asg-haystack` + compose) | Yes — CD family |
| Create or change infrastructure | No — infra project |
| Operate the live system (monitor, recover, `stop` / `destroy`) | No — infra project after go-live |

Operate comes after deploy. It requires knowledge of the infrastructure; it does not create it. App CD does not create the ASG.

## How to read the three frameworks

| Framework | Path | Role |
| --- | --- | --- |
| **OpenSpec** | [`../openspec/`](../openspec/) | Observable behavior: requirements and GIVEN/WHEN/THEN scenarios |
| **OpenSPDD** | [`../spdd/`](../spdd/) | Implementation contract: REASONS Canvas (how to write the YAML, what not to invent) |
| **ADR** | [`../docs/adr/`](../docs/adr/) | Why: caller gate, uv toolchain, env-driven Release image, Academy-only CD, masked Vocareum keys, reused Ansible |

Conflict order: **OpenSpec scenarios → OpenSPDD Safeguards → ADR → YAML**. If the YAML cannot satisfy a scenario without breaking a safeguard, stop and update the spec first.

## Changes

### CI family — [`../openspec/changes/add-haystack-ci-pipeline/`](../openspec/changes/add-haystack-ci-pipeline/)

- Proposal: [`proposal.md`](../openspec/changes/add-haystack-ci-pipeline/proposal.md)
- Design: [`design.md`](../openspec/changes/add-haystack-ci-pipeline/design.md)
- Tasks: [`tasks.md`](../openspec/changes/add-haystack-ci-pipeline/tasks.md)
- SPDD analysis: [`../spdd/analysis/add-haystack-ci-pipeline.md`](../spdd/analysis/add-haystack-ci-pipeline.md)
- REASONS Canvas: [`../spdd/prompt/add-haystack-ci-pipeline.md`](../spdd/prompt/add-haystack-ci-pipeline.md)
- Walkthrough: [`pipelines/haystack-ci.md`](pipelines/haystack-ci.md)
- Image contract: [ADR 0008](../docs/adr/0008-haystack-ci-release-image-env-driven.md)

### CD family — skeleton then deploy

- [`../openspec/changes/add-haystack-cd-academy-skeleton/`](../openspec/changes/add-haystack-cd-academy-skeleton/)
- [`../openspec/changes/add-haystack-cd-academy-deploy/`](../openspec/changes/add-haystack-cd-academy-deploy/)
- SPDD: [`../spdd/analysis/add-haystack-cd-academy-skeleton.md`](../spdd/analysis/add-haystack-cd-academy-skeleton.md), [`../spdd/analysis/add-haystack-cd-academy-deploy.md`](../spdd/analysis/add-haystack-cd-academy-deploy.md)
- Walkthrough: [`pipelines/haystack-cd.md`](pipelines/haystack-cd.md)
- Operator: [`../docs/BOOTSTRAP.md`](../docs/BOOTSTRAP.md), [`../docs/PREPARE-HAYSTACK-REPO.md`](../docs/PREPARE-HAYSTACK-REPO.md)

## Workflows (implementation)

| Pipeline | Reusable | Caller (install into the app repo) |
| --- | --- | --- |
| Fast feedback | [`../fast-feedback-ci-pipeline/fast-feedback-pipeline.yml`](../fast-feedback-ci-pipeline/fast-feedback-pipeline.yml) | [`haystack-fast-feedback-caller.yml`](../fast-feedback-ci-pipeline/haystack-fast-feedback-caller.yml) |
| Integration CI | [`../integration-pipeline/integration-pipeline.yml`](../integration-pipeline/integration-pipeline.yml) | [`haystack-ci-caller.yml`](../integration-pipeline/haystack-ci-caller.yml) |
| Release | [`../release-pipeline/release-pipeline.yml`](../release-pipeline/release-pipeline.yml) | [`haystack-release-caller.yml`](../release-pipeline/haystack-release-caller.yml) |
| Academy CD | [`../deploy-pipeline/haystack-cd-academy.yml`](../deploy-pipeline/haystack-cd-academy.yml) | [`haystack-cd-academy-caller.yml`](../deploy-pipeline/haystack-cd-academy-caller.yml) |
