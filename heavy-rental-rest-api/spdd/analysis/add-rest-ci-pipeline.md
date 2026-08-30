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
| Integration | Highest-priority job: checkout + Java 21 + Maven resolve + layout. Not “run tests”. Integration CI job id `integration-check` (name **Integration Check**); Fast Feedback and Release keep `integration`. Release always checks out `master`. PR Integration Check reuses Fast Feedback for the head SHA. |
| Quality Control | Compile + Spring tests against Docker Postgres + package WAR (build verification). Environment names are hardcoded (`integration` / `production`). |
| Security | Semgrep Java (exclude `.github/**`) + Semgrep GHA + Trivy CRITICAL gate — **Integration CI only** |
| Packaging | Versioned WAR + env-driven Tomcat image tar; `spring-datasource.env` not in the image. Does not `docker push`. |
| DAST | Release only: ZAP + Dastardly (gates) + Nuclei (report-only) + combined PDF |
| Publish | Release only: public GHCR + GitHub Release on `master` |
| `REST_API_DB_*` | Integration and Release: Repository secrets + caller explicit map (QC also uses Environment `integration` / `production`). Local Docker Postgres only |
| Guest SM | `heavy-rental/rest` on the instance — Academy CD, not this family |

## Stakeholders

- Spring developers (fast feedback + green PRs into `develop`)
- Release managers (`workflow_dispatch` on master; this job creates the GitHub Release)
- Academy CD operators (consume GHCR/tar; do not reuse CI DB secret names)

## Risks

1. **Wrong toolchain** — Node, uv, or Gradle on this family. Forbidden.
2. **Secret mix-up** — putting `REST_API_DB_*` on the guest or using them as Academy RDS.
3. **`environment:` on `uses:`** — invalid. Both callers forward Repository secrets via an explicit map; QC jobs still use Environment `integration` / `production`. No `secrets: inherit`.
4. **Scope creep** — Terraform or Ansible in CI YAML. Forbidden.

## Strategy

1. Specify as-implemented behavior in OpenSpec (including `rest-ci-scope`).
2. Bind implementation in this analysis + Canvas (negative space).
3. Keep the six GitHub Flow YAML files plus the Security Report pair as the implementation. The Security Report pair is reporting-only (not a merge gate).

## Success

- Six GitHub Flow YAML files plus the Security Report pair remain the implementation; specs match job names (`Integration Check` on CI) and secret names (both callers pass `REST_API_DB_*`). Security Report is documented as reporting-only.
- `specification/` indexes CI and CD.
- ADRs 0004–0007 record CI decisions (0007 = env-driven image); 0001–0003 and 0008 remain CD.
- Packaging refuses baked guest/CI-DB env and proves dummy `SPRING_DATASOURCE_URL` / `POSTGRES_HOST` / `HAYSTACK_BASE_URL` / Stripe / JWT.
