# Heavy Rental mobile pipelines — specification

This folder is the **human index** for the GitHub Actions family that lives in `heavy-rental-mobile/`.

The Android **product** specification (screens, domain, OpenAPI) is **not** here. It lives in the application repository:

https://github.com/Heavy-Rental/heavy-rental-mobile/tree/develop/specification

## How to read the two frameworks

| Framework | Path | Role |
| --- | --- | --- |
| **OpenSpec** | [`../openspec/`](../openspec/) | Observable behavior: requirements and GIVEN/WHEN/THEN scenarios |
| **OpenSPDD** | [`../spdd/`](../spdd/) | Implementation contract: REASONS Canvas (how to write the YAML, what not to invent) |

Conflict order: **OpenSpec scenarios → OpenSPDD Safeguards → YAML**. If the YAML cannot satisfy a scenario without breaking a safeguard, stop and update the spec first.

## Active change

[`../openspec/changes/add-mobile-ci-pipeline/`](../openspec/changes/add-mobile-ci-pipeline/) — first mobile CI family.

- Proposal: [`proposal.md`](../openspec/changes/add-mobile-ci-pipeline/proposal.md)
- Design: [`design.md`](../openspec/changes/add-mobile-ci-pipeline/design.md)
- Tasks: [`tasks.md`](../openspec/changes/add-mobile-ci-pipeline/tasks.md)
- SPDD analysis: [`../spdd/analysis/add-mobile-ci-pipeline.md`](../spdd/analysis/add-mobile-ci-pipeline.md)
- REASONS Canvas: [`../spdd/prompt/add-mobile-ci-pipeline.md`](../spdd/prompt/add-mobile-ci-pipeline.md)

Walkthrough of the pipelines themselves: [`pipelines/mobile-ci.md`](pipelines/mobile-ci.md).

## Workflows (implementation)

| Pipeline | Reusable | Caller (install into the app repo) |
| --- | --- | --- |
| Fast feedback | [`../fast-feedback-ci-pipeline/fast-feedback-pipeline.yml`](../fast-feedback-ci-pipeline/fast-feedback-pipeline.yml) | [`mobile-fast-feedback-caller.yml`](../fast-feedback-ci-pipeline/mobile-fast-feedback-caller.yml) |
| Integration CI | [`../integration-pipeline/integration-pipeline.yml`](../integration-pipeline/integration-pipeline.yml) | [`mobile-ci-caller.yml`](../integration-pipeline/mobile-ci-caller.yml) |
| Release | [`../release-pipeline/release-pipeline.yml`](../release-pipeline/release-pipeline.yml) | [`mobile-release-caller.yml`](../release-pipeline/mobile-release-caller.yml) |
