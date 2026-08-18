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
| Integration | Node 22 + `npm ci` + lockfile health. Not lint, not `vite build` |
| Quality Control | ESLint + `tsc -b` |
| REST Endpoint Tests | Local mock on `:4010`; skip-clean until scripts exist |
| Packaging | `dist/` zip + static nginx image (try_files); scan for secrets/lab URLs; GHCR off PR |
| `integration_pipeline/` | Authoring folder name (underscore). Install name stays `integration-pipeline.yml` |

## Stakeholders

- Portal developers (fast feedback + green PRs into `develop`)
- Release managers
- Academy CD operators (consume GHCR/tar)

## Risks

1. **Wrong toolchain** — Java, uv, or Gradle on this family.
2. **Authoring path** — docs saying `integration-pipeline/` for this tree.
3. **Live backend** — pointing REST tests at Academy ALB.
4. **Scope creep** — Terraform or Ansible in CI YAML.

## Strategy

Specify existing behavior. Do not invent new jobs.

## Success

- Specs match job names, Node 22, mock `127.0.0.1:4010`, and skip-clean REST tests.
- `specification/` indexes CI and CD.
- `PREPARE-PORTAL-REPO.md` exists.
- ADRs 0004–0007 record CI decisions (0007 = static SPA; CD owns `/api`); 0001–0003 remain CD.
- Packaging scans `dist/` and the image for `sk_` / localhost:8080|8000 and refuses baked `REST_BASE_URL` / `VITE_*`.
