# Heavy Rental — application GitHub Actions families

Reusable GitHub Actions for the Heavy Rental **application** pipelines: Fast Feedback, Integration CI, Release packaging, a scheduled Security Report (Haystack, REST, and portal), and (except mobile) Academy + paid app CD.

This tree does **not** provision the VPC, ASGs, RDS, or NAT. That is [`heavy-rental-project-instructure-and-cloud-deploy`](../heavy-rental-project-instructure-and-cloud-deploy/). Product behaviour (FastAPI, Spring, React, Android screens) lives in each application repository.

**Start here:** [`specification/README.md`](specification/README.md) (OpenSpec, OpenSPDD, ADR index per family). Conflict order: **OpenSpec scenarios → OpenSPDD Safeguards → ADR → YAML**.

| Path | Contents |
| --- | --- |
| `specification/` | Human index for all families |
| `haystack-fast-api-pipeline/` | Haystack FastAPI CI + Security Report + Academy/paid CD (compose workers match estate) |
| `heavy-rental-rest-api/` | Spring REST API CI + Security Report + Academy/paid CD |
| `heavy-rental-web-portal-pipeline/` | React portal CI + Security Report + Academy/paid CD |
| `heavy-rental-mobile/` | Android CI only (unsigned APK + MobSF; no app CD) |
| `cloud-deployment-feasibility-studies/` | Design records + as-built tables ([`cloud-deployment-feasibility-studies/README.md`](cloud-deployment-feasibility-studies/README.md)) |
| `scripts/` | Combined security / DAST PDF helpers (keep in sync with YAML heredocs) |
| `devcontainer/` | Devcontainer used to author and `actionlint` the YAML |

## GitHub Flow (each CI family)

```
feature branch push  →  Fast Feedback (Integration only; sole Integration-stage run for that SHA)
PR / push → develop  →  Integration CI (reuses Fast Feedback on PR, waits if in-flight; full gates; SAST here)
workflow_dispatch     →  Release (master + QC + package + DAST + publish)
```

Haystack, REST, and portal Release publish a public GHCR image and a GitHub Release. Mobile Release publishes an unsigned APK, MobSF DAST, and a GitHub Release (no GHCR). Haystack, REST, and portal also have a scheduled **Security Report** (Haystack and REST: Monday 06:00 UTC; portal: Monday 08:00 UTC; or manual). It summarizes existing Code Scanning alerts; it is **not** a merge gate.

Copy caller + reusable pairs from each family folder into the application repo `.github/workflows/`. This repo’s own `.github/workflows/` copies (if present) can lag; they are not the install source.

## App CD vs the estate

Portal / REST / Haystack **first compose** is infra `action=deploy-projects` (`site.yml`) or this tree’s app CD `action=deploy`. Infra `apply` / `configure-only` run `configure.yml` (Docker + Neo4j only) and do **not** compose the three apps.

Haystack, REST, and portal CD each have **two callers**: Environment `academy` (Vocareum) and Environment `AWS_ACTUAL` (OIDC). Mobile has no app CD.

App CD `verify` uses the same **paths** as estate ALB probes: REST `GET :8080/actuator/health` **2xx** (ALB matcher `200-299`); Haystack `GET :8000/health` **2xx** (ALB matcher `200-299`); portal `GET :80/` **200 / 301 / 302** (ALB `tg-portal` matcher is `200-399`). Portal **Release Packaging** uses Environment `academy` only to bake Stripe `pk_`; that is not CD auth.

Haystack compose workers are `postgres:17` + `sync-from-primary.sh` and `python:3.12-slim` + `populate-neo4j-from-haystack.sh` (wraps `populate_neo4j.py`; Haystack ADR 0011 / infra ADR 0020). They are not `python -m` on the uvicorn image. Worker failure does not fail Haystack `verify`.

GHCR names (Publish after DAST): `haystack_recommender`, `heavy_rental_rest_api`, `heavy_rental_web_portal` (`:<semver>` + `:latest`). REST ALB is internet-facing `:8080`; Haystack ALB stays internal. Portal nginx `/api` hairpins to that REST DNS and **omits `Origin`**; Spring `APP_CORS_ALLOWED_ORIGINS` is for **direct** REST ALB callers, not the same-origin hairpin.

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
