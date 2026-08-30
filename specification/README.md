# Specification (pipeline-development)

This folder is the **human index** for GitHub Actions families authored in `heavy-rental-project-pipeline-development/`.

Infrastructure (VPC, ASGs, RDS, NAT, observe, `stop` / `destroy`) is **not** specified here. It belongs to `heavy-rental-project-instructure-and-cloud-deploy` — start at [`../../heavy-rental-project-instructure-and-cloud-deploy/specification/README.md`](../../heavy-rental-project-instructure-and-cloud-deploy/specification/README.md).

Product behaviour (FastAPI, Spring, React, Android screens) is **not** here. It lives in each application repository.

## Pipeline boundaries

| Concern | Specified here? |
| --- | --- |
| Fast Feedback, Integration CI, Release packaging | Yes — per family |
| Security Report (Haystack, REST, portal) | Yes — scheduled/manual summary; not a merge gate |
| Academy + paid app CD (Haystack, REST, portal) | Yes — discover ASG + compose |
| Create or change infrastructure | No — infra project |
| Operate the live system (`stop` / `destroy`) | No — infra project after go-live |
| Mobile Play signing / store CD / GHCR | No |

## How to read the three frameworks

| Framework | Role |
| --- | --- |
| **OpenSpec** | Observable behavior: SHALL + GIVEN/WHEN/THEN, under each family’s `openspec/` |
| **OpenSPDD** | REASONS Canvas (how to write the YAML, what not to invent), under each family’s `spdd/` |
| **ADR** | Why, under each family’s `docs/adr/` |

Conflict order: **OpenSpec scenarios → OpenSPDD Safeguards → ADR → YAML**. If YAML cannot satisfy a scenario without breaking a safeguard, update the spec first.

`cloud-deployment-feasibility-studies/` are **design records with as-built tables**. Start at [`../cloud-deployment-feasibility-studies/README.md`](../cloud-deployment-feasibility-studies/README.md). Living behavior is still the per-family OpenSpec / OpenSPDD / ADR trees. If a study body disagrees with an as-built table or an ADR, the table / ADR / YAML wins.

## As-implemented (read this first)

| Topic | Fact |
| --- | --- |
| CI GitHub Flow | Feature push → Fast Feedback (Integration only). PR / push `develop` → Integration CI (reuses Fast Feedback on PR, waits if in-flight). `workflow_dispatch` → Release (checkout `master`) |
| Release | Dispatch only. Haystack / REST / portal: Packaging writes the image tar; **Publish** pushes public GHCR + creates the GitHub Release. **Mobile:** unsigned APK + MobSF + GitHub Release (no tar, no GHCR). SAST/CodeQL stay on Integration CI |
| GHCR | `haystack_recommender`, `heavy_rental_rest_api`, `heavy_rental_web_portal` (`:<semver>` + `:latest`). Mobile: unsigned APK, no GHCR |
| App CD callers | Haystack, REST, portal: Environment `academy` (Vocareum) and `AWS_ACTUAL` (OIDC). Mobile: none |
| First-compose | Infra `deploy-projects` (`site.yml`) or app CD `action=deploy`. Infra `apply` / `configure-only` do **not** compose the three apps |
| REST ALB | Internet-facing `:8080`. Haystack ALB, Bolt NLB, and RDS stay internal |
| ALB / CD health | REST `GET :8080/actuator/health` **2xx**; Haystack `GET :8000/health` **2xx**; portal ALB `GET :80/` matcher `200-399`, app CD `verify` accepts **200 / 301 / 302** |
| Haystack workers | `postgres:17` + `sync-from-primary.sh` and `python:3.12-slim` + `populate-neo4j-from-haystack.sh` (wraps `populate_neo4j.py`; Haystack ADR 0011 / infra ADR 0020). Not uvicorn `-m`. Worker failure does not fail `verify` |
| Portal Stripe | Release Packaging Environment `academy` bakes `pk_` only. `sk_` never lands on the portal |
| Security Report | Haystack, REST, and portal. Haystack/REST Monday 06:00 UTC; portal Monday 08:00 UTC; or manual. Not a merge gate |

Estate layout and ALB probes: [`../../heavy-rental-project-instructure-and-cloud-deploy/docs/ARCHITECTURE.md`](../../heavy-rental-project-instructure-and-cloud-deploy/docs/ARCHITECTURE.md). Haystack estate workers: infra [`add-infra-haystack-workers`](../../heavy-rental-project-instructure-and-cloud-deploy/openspec/changes/add-infra-haystack-workers/) / [ADR 0020](../../heavy-rental-project-instructure-and-cloud-deploy/docs/adr/0020-haystack-devcontainer-workers.md).

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
