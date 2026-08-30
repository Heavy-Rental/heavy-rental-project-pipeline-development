# SPDD Analysis: add-portal-ci-pipeline

**Status:** Active (as-implemented)  
**Audience:** Maintainers of the web portal GitHub Actions family  
**Companion:** [REASONS Canvas](../prompt/add-portal-ci-pipeline.md) · [OpenSpec change](../../openspec/changes/add-portal-ci-pipeline/proposal.md)

## Problem

Portal Fast Feedback / Integration / Release YAML already exists. Haystack and mobile have OpenSpec + OpenSPDD + ADRs for the same family. Portal CI was headers-only.

## Concepts

| Concept | Meaning here |
| --- | --- |
| Caller | Workflow that only `uses:` a sibling reusable file |
| Reusable pipeline | `on: workflow_call` only; `assert-caller` rejects any other file |
| Integration | Highest-priority job: checkout + Node 22 + `npm ci` + lockfile health. Not lint, not `vite build`. Integration CI job id `integration-check` (name **Integration Check**); Fast Feedback and Release keep `integration`. Release always checks out `master`. PR Integration Check reuses Fast Feedback for the head SHA (wait if in-flight; inlined pending-run jq; no `PENDING_FILTER`). |
| Quality Control | ESLint + `tsc -b` |
| REST Endpoint Tests | Local mock on `:4010`; skip-clean until scripts exist |
| Packaging | `dist/` zip + static nginx image tar (try_files); scan for secrets/lab URLs; no `docker push` |
| DAST | ZAP + Dastardly (gates) + Nuclei (report-only) against the packaged image |
| Publish | GHCR `heavy_rental_web_portal:<semver>` + `:latest` and GitHub Release on `master` |
| `integration_pipeline/` | Authoring folder name (underscore). Install name stays `integration-pipeline.yml` |

## Stakeholders

- Portal developers (fast feedback + green PRs into `develop`)
- Release managers (dispatch Release after merge to `master`)
- Academy CD operators (consume GHCR/tar)

## Risks

1. **Wrong toolchain** — Java, uv, or Gradle on this family.
2. **Authoring path** — docs saying `integration-pipeline/` for this tree.
3. **Live backend** — pointing REST tests at Academy ALB.
4. **Scope creep** — Terraform or Ansible in CI YAML.
5. **Stale Release trigger** — documenting `on: release` or a `develop` → `master` PR; Publish creates the GitHub Release.

## Strategy

Specify as-implemented behavior. Keep the six GitHub Flow YAML files plus the Security Report pair as the implementation. The Security Report pair is reporting-only (not a merge gate).

## Success

- Six GitHub Flow YAML files plus the Security Report pair remain the implementation; specs match job names (`Integration Check` on CI), Node 22, mock `127.0.0.1:4010`, and skip-clean REST tests. Security Report is documented as reporting-only.
- Release is `workflow_dispatch` only: Integration → QC → Packaging → DAST → Publish.
- `specification/` indexes CI and CD.
- `PREPARE-PORTAL-REPO.md` exists.
- ADRs 0004–0008 record CI decisions (0007 = static SPA; 0008 = Vite `.env.production` vs AWS/Spring REST); 0001–0003 remain CD.
- Packaging seeds/scans `.env.production` (scan input; `--mode api` loads `.env.api`), then `vite build --mode api` with empty `VITE_API_TARGET`, scans `dist/` / image for `sk_` / localhost / `heavy-rental-rest-api`, and refuses image `COPY .env`.
- `docs/samples/.env.production` exists for operators to copy into the React repo (Release **scan** input; `--mode api` loads `.env.api`).
