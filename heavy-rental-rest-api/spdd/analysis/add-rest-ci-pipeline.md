# SPDD Analysis: add-rest-ci-pipeline

**Status:** Active (as-implemented)  
**Audience:** Maintainers of the REST API GitHub Actions family  
**Companion:** [REASONS Canvas](../prompt/add-rest-ci-pipeline.md) · [OpenSpec change](../../openspec/changes/add-rest-ci-pipeline/proposal.md)

## Problem

REST Fast Feedback / Integration / Release YAML already exists. Haystack and mobile have OpenSpec + OpenSPDD + ADRs for the same family. REST CI was headers-only, so edits had no behavior contract.

## Concepts

| Concept | Meaning here |
| --- | --- |
| Caller | Workflow with `on: push/pull_request/release` that only `uses:` a sibling reusable file |
| Reusable pipeline | `on: workflow_call` only; `assert-caller` rejects any other file |
| Integration | Highest-priority job: checkout + Java 21 + Maven resolve + layout. Not “run tests” |
| Quality Control | Compile + Spring tests against Docker Postgres + package WAR (build verification) |
| Security | Semgrep Java + Trivy CRITICAL gate |
| Packaging | Versioned WAR + env-driven Tomcat image tar; GHCR off PR; `spring-datasource.env` not in the image |
| `REST_API_DB_*` | Integration CI Environment `integration` — local Docker Postgres only |
| `REST_API_CLOUD_DB_*` | Release Environment `production` — local Docker Postgres + cloud JDBC artifact (no password) |
| Guest SM | `heavy-rental/rest` on the instance — Academy CD, not this family |

## Stakeholders

- Spring developers (fast feedback + green PRs into `develop`)
- Release managers (`develop` → `master` / GitHub Release)
- Academy CD operators (consume GHCR/tar; do not reuse CI DB secret names)

## Risks

1. **Wrong toolchain** — Node, uv, or Gradle on this family. Forbidden.
2. **Secret mix-up** — putting `REST_API_CLOUD_DB_*` on the guest or using them as Integration CI secrets.
3. **`environment:` on `uses:`** — invalid; explicit secrets map only.
4. **Scope creep** — Terraform or Ansible in CI YAML. Forbidden.

## Strategy

1. Specify existing behavior in OpenSpec (including `rest-ci-scope`).
2. Bind implementation in this analysis + Canvas (negative space).
3. Do not invent new jobs.

## Success

- Six YAML files remain the implementation; specs match job names and secret names.
- `specification/` indexes CI and CD.
- ADRs 0004–0007 record CI decisions (0007 = env-driven image); 0001–0003 remain CD.
- Packaging refuses baked guest/CI-DB env and proves dummy `SPRING_DATASOURCE_URL` / `POSTGRES_HOST` / `HAYSTACK_BASE_URL` / Stripe / JWT.
