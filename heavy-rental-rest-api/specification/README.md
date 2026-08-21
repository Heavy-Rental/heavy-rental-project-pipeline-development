# Heavy Rental REST API pipelines — specification

This folder is the **human index** for the GitHub Actions family authored in `heavy-rental-rest-api/`.

The Spring **product** specification is **not** here. It lives in the application repository:

https://github.com/Heavy-Rental/heavy-rental-spring-rest-api

Infrastructure setup (VPC, ASGs, RDS) is **not** specified here. It belongs to the infra project. This tree authors **CI + Release packaging** and **Academy app CD**.

## Pipeline boundaries

| Concern | Specified here? |
| --- | --- |
| Fast Feedback, Integration CI, Release packaging | Yes — CI family |
| Academy app CD (discover `asg-rest` + compose) | Yes — CD family |
| Create or change infrastructure | No — infra project |
| Operate the live system (`stop` / `destroy`) | No — infra project after go-live |

## How to read the three frameworks

| Framework | Path | Role |
| --- | --- | --- |
| **OpenSpec** | [`../openspec/`](../openspec/) | Observable behavior: requirements and GIVEN/WHEN/THEN scenarios |
| **OpenSPDD** | [`../spdd/`](../spdd/) | Implementation contract: REASONS Canvas (how to write the YAML, what not to invent) |
| **ADR** | [`../docs/adr/`](../docs/adr/) | Why: caller gate, Environment secrets split, env-driven Tomcat image (0007), Academy-only CD, masked keys |

Conflict order: **OpenSpec scenarios → OpenSPDD Safeguards → ADR → YAML**. If the YAML cannot satisfy a scenario without breaking a safeguard, stop and update the spec first.

## Changes

### CI family — [`../openspec/changes/add-rest-ci-pipeline/`](../openspec/changes/add-rest-ci-pipeline/)

As-implemented spec of the existing Fast Feedback / Integration / Release YAML.

- Proposal: [`proposal.md`](../openspec/changes/add-rest-ci-pipeline/proposal.md)
- Design: [`design.md`](../openspec/changes/add-rest-ci-pipeline/design.md)
- Tasks: [`tasks.md`](../openspec/changes/add-rest-ci-pipeline/tasks.md)
- SPDD analysis: [`../spdd/analysis/add-rest-ci-pipeline.md`](../spdd/analysis/add-rest-ci-pipeline.md)
- REASONS Canvas: [`../spdd/prompt/add-rest-ci-pipeline.md`](../spdd/prompt/add-rest-ci-pipeline.md)
- Walkthrough: [`pipelines/rest-ci.md`](pipelines/rest-ci.md)
- Image contract: [ADR 0007](../docs/adr/0007-rest-ci-release-image-env-driven.md)

### CD family — skeleton then deploy

- [`../openspec/changes/add-rest-cd-academy-skeleton/`](../openspec/changes/add-rest-cd-academy-skeleton/)
- [`../openspec/changes/add-rest-cd-academy-deploy/`](../openspec/changes/add-rest-cd-academy-deploy/)
- SPDD: [`../spdd/analysis/add-rest-cd-academy-skeleton.md`](../spdd/analysis/add-rest-cd-academy-skeleton.md), [`../spdd/analysis/add-rest-cd-academy-deploy.md`](../spdd/analysis/add-rest-cd-academy-deploy.md)
- Walkthrough: [`pipelines/rest-cd.md`](pipelines/rest-cd.md)
- Operator: [`../docs/BOOTSTRAP.md`](../docs/BOOTSTRAP.md), [`../docs/PREPARE-SPRING-REPO.md`](../docs/PREPARE-SPRING-REPO.md)

## Workflows (implementation)

| Pipeline | Reusable | Caller (install into the app repo) |
| --- | --- | --- |
| Fast feedback | [`../fast-feedback-ci-pipeline/fast-feedback-pipeline.yml`](../fast-feedback-ci-pipeline/fast-feedback-pipeline.yml) | [`rest-api-fast-feedback-caller.yml`](../fast-feedback-ci-pipeline/rest-api-fast-feedback-caller.yml) |
| Integration CI | [`../integration-pipeline/integration-pipeline.yml`](../integration-pipeline/integration-pipeline.yml) | [`rest-api-ci-caller.yml`](../integration-pipeline/rest-api-ci-caller.yml) |
| Release | [`../release-pipeline/release-pipeline.yml`](../release-pipeline/release-pipeline.yml) | [`rest-api-release-caller.yml`](../release-pipeline/rest-api-release-caller.yml) |
| Academy CD | [`../deploy-pipeline/rest-api-cd-academy.yml`](../deploy-pipeline/rest-api-cd-academy.yml) | [`rest-api-cd-academy-caller.yml`](../deploy-pipeline/rest-api-cd-academy-caller.yml) |
| Paid CD | same reusable | [`rest-api-cd-paid-caller.yml`](../deploy-pipeline/rest-api-cd-paid-caller.yml) |
