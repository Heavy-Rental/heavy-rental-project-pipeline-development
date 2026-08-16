# Heavy Rental haystack-fast-api pipelines — specification

This folder is the **human index** for the GitHub Actions family authored in `haystack-fast-api-pipeline/`.

The FastAPI / Haystack **product** specification (Call 1 / Call 2 / indexing / OpenAPI) is **not** here. It lives in the application repository:

https://github.com/Heavy-Rental/haystack-fast-api/tree/develop/openspec

Infrastructure setup, project deployment, and operate workflows are **not** specified here. They belong to another project. This family ends at CI gates and Release packaging.

## Pipeline boundaries

| Concern | Specified here? |
| --- | --- |
| Fast Feedback, Integration CI, Release packaging | Yes |
| Create or change infrastructure | No — another project |
| Deploy packaged artifacts | No — another project |
| Operate the live system (monitor, recover) | No — another project |

Operate comes after deploy. It requires knowledge of the infrastructure; it does not create it.

## How to read the two frameworks

| Framework | Path | Role |
| --- | --- | --- |
| **OpenSpec** | [`../openspec/`](../openspec/) | Observable behavior: requirements and GIVEN/WHEN/THEN scenarios |
| **OpenSPDD** | [`../spdd/`](../spdd/) | Implementation contract: REASONS Canvas (how to write the YAML, what not to invent) |

Conflict order: **OpenSpec scenarios → OpenSPDD Safeguards → YAML**. If the YAML cannot satisfy a scenario without breaking a safeguard, stop and update the spec first.

## Active change

[`../openspec/changes/add-haystack-ci-pipeline/`](../openspec/changes/add-haystack-ci-pipeline/) — first haystack CI family.

- Proposal: [`proposal.md`](../openspec/changes/add-haystack-ci-pipeline/proposal.md)
- Design: [`design.md`](../openspec/changes/add-haystack-ci-pipeline/design.md)
- Tasks: [`tasks.md`](../openspec/changes/add-haystack-ci-pipeline/tasks.md)
- SPDD analysis: [`../spdd/analysis/add-haystack-ci-pipeline.md`](../spdd/analysis/add-haystack-ci-pipeline.md)
- REASONS Canvas: [`../spdd/prompt/add-haystack-ci-pipeline.md`](../spdd/prompt/add-haystack-ci-pipeline.md)

Walkthrough of the pipelines themselves: [`pipelines/haystack-ci.md`](pipelines/haystack-ci.md).

## Workflows (implementation)

| Pipeline | Reusable | Caller (install into the app repo) |
| --- | --- | --- |
| Fast feedback | [`../fast-feedback-ci-pipeline/fast-feedback-pipeline.yml`](../fast-feedback-ci-pipeline/fast-feedback-pipeline.yml) | [`haystack-fast-feedback-caller.yml`](../fast-feedback-ci-pipeline/haystack-fast-feedback-caller.yml) |
| Integration CI | [`../integration-pipeline/integration-pipeline.yml`](../integration-pipeline/integration-pipeline.yml) | [`haystack-ci-caller.yml`](../integration-pipeline/haystack-ci-caller.yml) |
| Release | [`../release-pipeline/release-pipeline.yml`](../release-pipeline/release-pipeline.yml) | [`haystack-release-caller.yml`](../release-pipeline/haystack-release-caller.yml) |
