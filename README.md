# Heavy Rental — application GitHub Actions families

Reusable GitHub Actions for the Heavy Rental **application** pipelines: Fast Feedback, Integration CI, Release packaging, and (except mobile) Academy + paid app CD.

This tree does **not** provision the VPC, ASGs, RDS, or NAT. That is [`heavy-rental-project-instructure-and-cloud-deploy`](../heavy-rental-project-instructure-and-cloud-deploy/). Product behaviour (FastAPI, Spring, React, Android screens) lives in each application repository.

**Start here:** [`specification/README.md`](specification/README.md) (OpenSpec, OpenSPDD, ADR index per family). Conflict order: **OpenSpec scenarios → OpenSPDD Safeguards → ADR → YAML**.

| Path | Contents |
| --- | --- |
| `specification/` | Human index for all families |
| `haystack-fast-api-pipeline/` | Haystack FastAPI CI + Academy/paid CD |
| `heavy-rental-rest-api/` | Spring REST API CI + Academy/paid CD |
| `heavy-rental-web-portal-pipeline/` | React portal CI + Academy/paid CD |
| `heavy-rental-mobile/` | Android CI only (unsigned APK + MobSF; no app CD) |
| `cloud-deployment-feasibility-studies/` | Design records + as-built tables ([`cloud-deployment-feasibility-studies/README.md`](cloud-deployment-feasibility-studies/README.md)) |
| `scripts/` | Combined security / DAST PDF helpers (keep in sync with YAML heredocs) |
| `devcontainer/` | Devcontainer used to author and `actionlint` the YAML |

## GitHub Flow (each CI family)

```
feature branch push  →  Fast Feedback (Integration only)
PR / push → develop  →  Integration CI (full gates; SAST here)
workflow_dispatch     →  Release (master + QC + package + DAST + publish)
```

Haystack, REST, and portal Release publish a public GHCR image and a GitHub Release. Mobile Release publishes an unsigned APK, MobSF DAST, and a GitHub Release (no GHCR).

Haystack, REST, and portal CD each have **two callers**: Environment `academy` (Vocareum) and Environment `AWS_ACTUAL` (OIDC). Copy caller + reusable pairs into the application repo `.github/workflows/`.

App CD `verify` uses the same **paths** as estate ALB probes: REST `GET :8080/actuator/health` **2xx** (ALB matcher `200-299`); Haystack `GET :8000/health` **2xx** (ALB matcher `200-299`); portal `GET :80/` **200 / 301 / 302** (ALB `tg-portal` matcher is `200-399`). Portal **Release Packaging** uses Environment `academy` only to bake Stripe `pk_`; that is not CD auth.

## Families

| Family | Application | Human index |
| --- | --- | --- |
| Haystack CI + CD | [haystack-fast-api](https://github.com/Heavy-Rental/haystack-fast-api) | [`haystack-fast-api-pipeline/specification/`](haystack-fast-api-pipeline/specification/) |
| REST CI + CD | [heavy-rental-spring-rest-api](https://github.com/Heavy-Rental/heavy-rental-spring-rest-api) | [`heavy-rental-rest-api/specification/`](heavy-rental-rest-api/specification/) |
| Portal CI + CD | [heavy-rental-react-web-portal](https://github.com/Heavy-Rental/heavy-rental-react-web-portal) | [`heavy-rental-web-portal-pipeline/specification/`](heavy-rental-web-portal-pipeline/specification/) |
| Mobile CI | [heavy-rental-mobile](https://github.com/Heavy-Rental/heavy-rental-mobile) | [`heavy-rental-mobile/specification/`](heavy-rental-mobile/specification/) |

## Out of scope

- Terraform / Ansible estate (`heavy-rental-project-instructure-and-cloud-deploy`)
- Product OpenSpec in the application repositories
- Play signing, emulator tests, or mobile store CD
