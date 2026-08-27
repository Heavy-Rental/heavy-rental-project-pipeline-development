# Specification (pipeline-development)

This folder is the **human index** for GitHub Actions families authored in `heavy-rental-project-pipeline-development/`.

Infrastructure (VPC, ASGs, RDS, NAT, observe, `stop` / `destroy`) is **not** specified here. It belongs to `heavy-rental-project-instructure-and-cloud-deploy` — start at [`../../heavy-rental-project-instructure-and-cloud-deploy/specification/README.md`](../../heavy-rental-project-instructure-and-cloud-deploy/specification/README.md).

Product behaviour (FastAPI, Spring, React, Android screens) is **not** here. It lives in each application repository.

## How to read the three frameworks

| Framework | Role |
| --- | --- |
| **OpenSpec** | Observable behavior: SHALL + GIVEN/WHEN/THEN, under each family’s `openspec/` |
| **OpenSPDD** | REASONS Canvas (how to write the YAML, what not to invent), under each family’s `spdd/` |
| **ADR** | Why, under each family’s `docs/adr/` |

Conflict order: **OpenSpec scenarios → OpenSPDD Safeguards → ADR → YAML**. If YAML cannot satisfy a scenario without breaking a safeguard, update the spec first.

`cloud-deployment-feasibility-studies/` are **design records with as-built tables**. Start at [`../cloud-deployment-feasibility-studies/README.md`](../cloud-deployment-feasibility-studies/README.md). Living behavior is still the per-family OpenSpec / OpenSPDD / ADR trees. If a study body disagrees with an as-built table or an ADR, the table / ADR / YAML wins.

## Families

| Family | Human index | OpenSpec | OpenSPDD | ADRs |
| --- | --- | --- | --- | --- |
| Haystack CI + CD | [`../haystack-fast-api-pipeline/specification/`](../haystack-fast-api-pipeline/specification/) | [`openspec/`](../haystack-fast-api-pipeline/openspec/) | [`spdd/`](../haystack-fast-api-pipeline/spdd/) | [`docs/adr/`](../haystack-fast-api-pipeline/docs/adr/) |
| REST CI + CD | [`../heavy-rental-rest-api/specification/`](../heavy-rental-rest-api/specification/) | [`openspec/`](../heavy-rental-rest-api/openspec/) | [`spdd/`](../heavy-rental-rest-api/spdd/) | [`docs/adr/`](../heavy-rental-rest-api/docs/adr/) |
| Portal CI + CD | [`../heavy-rental-web-portal-pipeline/specification/`](../heavy-rental-web-portal-pipeline/specification/) | [`openspec/`](../heavy-rental-web-portal-pipeline/openspec/) | [`spdd/`](../heavy-rental-web-portal-pipeline/spdd/) | [`docs/adr/`](../heavy-rental-web-portal-pipeline/docs/adr/) |
| Mobile CI only | [`../heavy-rental-mobile/specification/`](../heavy-rental-mobile/specification/) | [`openspec/`](../heavy-rental-mobile/openspec/) | [`spdd/`](../heavy-rental-mobile/spdd/) | [`docs/adr/`](../heavy-rental-mobile/docs/adr/) |

Haystack, REST, and portal CD each have **two callers**: Environment `academy` (Vocareum) and Environment `AWS_ACTUAL` (OIDC). Mobile has no app CD.

## Walkthroughs

- [`../haystack-fast-api-pipeline/specification/pipelines/haystack-ci.md`](../haystack-fast-api-pipeline/specification/pipelines/haystack-ci.md) · [`haystack-cd.md`](../haystack-fast-api-pipeline/specification/pipelines/haystack-cd.md)
- [`../heavy-rental-rest-api/specification/pipelines/rest-ci.md`](../heavy-rental-rest-api/specification/pipelines/rest-ci.md) · [`rest-cd.md`](../heavy-rental-rest-api/specification/pipelines/rest-cd.md)
- [`../heavy-rental-web-portal-pipeline/specification/pipelines/portal-ci.md`](../heavy-rental-web-portal-pipeline/specification/pipelines/portal-ci.md) · [`portal-cd.md`](../heavy-rental-web-portal-pipeline/specification/pipelines/portal-cd.md)
- [`../heavy-rental-mobile/specification/pipelines/mobile-ci.md`](../heavy-rental-mobile/specification/pipelines/mobile-ci.md)
