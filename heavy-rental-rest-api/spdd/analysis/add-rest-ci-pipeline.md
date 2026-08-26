# SPDD Analysis: add-rest-ci-pipeline

**Status:** Active (as-implemented)  
**Audience:** Maintainers of the REST API GitHub Actions family  
**Companion:** [REASONS Canvas](../prompt/add-rest-ci-pipeline.md) · [OpenSpec change](../../openspec/changes/add-rest-ci-pipeline/proposal.md)

## Problem

REST Fast Feedback / Integration / Release YAML already exists. Haystack and mobile have OpenSpec + OpenSPDD + ADRs for the same family. REST CI was headers-only, so edits had no behavior contract.

## Concepts

| Concept | Meaning here |
| --- | --- |
| Caller | Workflow that only `uses:` a sibling reusable file (Fast Feedback: push except master/develop; Integration CI: PR/push develop; Release: `workflow_dispatch` only) |
| Reusable pipeline | `on: workflow_call` only; `assert-caller` rejects any other file |
| Integration | Highest-priority job: checkout + Java 21 + Maven resolve + layout. Not “run tests”. Release always checks out `master`. |
| Quality Control | Compile + Spring tests against Docker Postgres + package WAR (build verification). Environment names are hardcoded (`integration` / `production`). |
| Security | Semgrep Java + Trivy CRITICAL gate — **Integration CI only** |
| Packaging | Versioned WAR + env-driven Tomcat image tar; `spring-datasource.env` not in the image. Does not `docker push`. |
| DAST | Release only: ZAP + Dastardly (gates) + Nuclei (report-only) + combined PDF |
| Publish | Release only: public GHCR + GitHub Release on `master` |
| `REST_API_DB_*` | Integration Environment `integration` and Release Environment `production` — local Docker Postgres only |
| Guest SM | `heavy-rental/rest` on the instance — Academy CD, not this family |

## Stakeholders

- Spring developers (fast feedback + green PRs into `develop`)
- Release managers (`workflow_dispatch` on master; this job creates the GitHub Release)
- Academy CD operators (consume GHCR/tar; do not reuse CI DB secret names)

## Risks

1. **Wrong toolchain** — Node, uv, or Gradle on this family. Forbidden.
2. **Secret mix-up** — putting `REST_API_DB_*` on the guest or using them as Academy RDS.
3. **`environment:` on `uses:`** — invalid; QC reads Environment secrets; no caller map and no inherit.
4. **Scope creep** — Terraform or Ansible in CI YAML. Forbidden.

## Strategy

1. Specify existing behavior in OpenSpec (including `rest-ci-scope`).
2. Bind implementation in this analysis + Canvas (negative space).
3. Do not invent new jobs.

## Success

- Six YAML files remain the implementation; specs match job names and secret names.
- `specification/` indexes CI and CD.
- ADRs 0004–0007 record CI decisions (0007 = env-driven image); 0001–0003 and 0008 remain CD.
- Packaging refuses baked guest/CI-DB env and proves dummy `SPRING_DATASOURCE_URL` / `POSTGRES_HOST` / `HAYSTACK_BASE_URL` / Stripe / JWT.
