# SPDD Analysis: add-haystack-ci-pipeline

**Status:** Active  
**Audience:** Implementers of the haystack-fast-api GitHub Actions family  
**Companion:** [REASONS Canvas](../prompt/add-haystack-ci-pipeline.md) · [OpenSpec change](../../openspec/changes/add-haystack-ci-pipeline/proposal.md)

## Problem

`Heavy-Rental/haystack-fast-api` has no CI. The organization already standardized on a reusable-caller GitHub Flow family for the Spring REST API, the React portal, and the Android app. Copy-pasting those YAML files unchanged would install the **wrong toolchain** (Java 21 + Maven + Postgres, Node 22 + Vite, or JDK 17 + Android SDK).

The application is already a uv project: Python 3.12, `uv.lock`, Ruff, pytest, Haystack pipelines that construct with mock/memory/stub backends.

Infrastructure setup, project deployment, and operate are another project's problem. This change must not invent those workflows here.

## Concepts

| Concept | Meaning here |
| --- | --- |
| Caller | Workflow with `on: push/pull_request/workflow_dispatch` that only `uses:` a sibling reusable file |
| Reusable pipeline | `on: workflow_call` only; `assert-caller` rejects any other file |
| Integration | Highest-priority job: checkout + CPython 3.12 + uv + Haystack pipeline smoke. On PR, reuse Fast Feedback for the head SHA instead of repeating uv/layout. Not “run pytest” |
| Quality Control | Ruff + pytest (Haystack + FastAPI TestClient). Not live pgvector, not LLM eval |
| Security | Semgrep app + GHA (two passes) + pip-audit report + Trivy CRITICAL gate |
| Packaging | `uv build` wheel/sdist plus env-driven Docker image tar (sanitized `.env.prod` → `/app/.env`). Publish (after DAST) pushes GHCR and creates the GitHub Release |
| Infrastructure | Create or change the platform (IaC). Infra project. Not this CI family |
| Deploy | Put Release artifacts onto existing infrastructure. Academy CD in `deploy-pipeline/` |
| Operate | Keep the live system healthy after deploy. Needs infra knowledge; does not create infra. Another project |

## Stakeholders

- Haystack/FastAPI developers (need fast feedback on feature branches and green PRs into `develop`)
- Pipeline authors in this repo (must keep REST/portal/mobile conventions)
- Release managers (`workflow_dispatch` of Haystack Release Pipeline Invoke on `master`)
- Authors of the later infrastructure / deploy / operate project (consume artifacts; not blocked on this family implementing IaC)

## Risks

1. **Wrong toolchain** — inheriting Java, Gradle, Node, or Maven. Forbidden.
2. **Secrets theatre** — inventing `environment: integration`, `REST_API_DB_*`, or `LLM_API_KEY`. The unmarked pytest suite is CI-safe without them.
3. **Live backend spend** — `RUN_PGVECTOR_TESTS`, `RUN_NEO4J_TESTS`, or `NEED_DECOMPOSER=llm`. Forbidden in v1.
4. **Inventing a Dockerfile in the application repo** — do not commit one here. Release always generates the uvicorn image; an app `Dockerfile` is not the GHCR/CD image. Env-driven (ADR 0008 / 0009): no estate/`ENV`/`ARG`; sanitized `.env.prod` → `/app/.env` for product knobs; academy Environment vars are CD-only.
5. **Semgrep injection** — interpolating `${{ github.* }}` / `${{ inputs.* }}` inside `run:` scripts.
6. **Caller bypass** — a reusable file with `push:` in addition to `workflow_call`.
7. **Scope creep into another project** — Terraform/Bicep, rollout jobs, or operate monitors in this tree. Forbidden.

## Strategy

1. Specify behavior in OpenSpec (observable SHALL + scenarios), including `haystack-ci-scope`.
2. Bind implementation in this REASONS analysis + Canvas (operations, norms, negative space).
3. Clone REST/mobile **structure** (headers, gate, checkout resolver, SARIF two-pass) and replace the toolchain with uv / Ruff / pytest / Haystack.
4. Author files under `haystack-fast-api-pipeline/` so the Python family is self-contained.

## Success

- Six YAML files exist, `actionlint`-clean, Semgrep-safe.
- Job names match the branch-protection list in the CI caller header.
- Toolchain is Python 3.12 + uv + Ruff + pytest + Haystack smoke.
- Release Packaging always generates uvicorn `app.main:app :8000` (`--extra neo4j`), sanitizes `.env.prod` → `/app/.env` (estate keys and `LLM_API_KEY` stripped), refuses `ENV`/`ARG` and raw `COPY .env`, proves dummy `-e` injection (process env wins) and `GET /docs` or `/health`, copies sidecar dirs only if present, and uploads a gzipped tar. DAST scans that image. Publish pushes GHCR `haystack_recommender` and creates the GitHub Release. Packaging does not read Environment `academy` and does not `docker push`. Fast Feedback and Integration CI still have no `packages: write`. The Release caller is `workflow_dispatch` only.
- No LLM/Postgres/Neo4j secrets in CI.
- Specs and headers name `haystack-fast-api-pipeline/` as the authoring tree and `Heavy-Rental/haystack-fast-api` as the application.
- No infrastructure, compose, or operate jobs in this CI family (ADR 0007–0008).
