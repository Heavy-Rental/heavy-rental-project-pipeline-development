# Design: Haystack FastAPI GitHub Actions CI family

## Context

This pipeline-development repo already authors REST API, web-portal, and mobile workflows as **reusable `workflow_call` files + sole-allowed callers**. The Haystack service is Python 3.12, packaged with uv (`pyproject.toml` + `uv.lock`), served by FastAPI/Uvicorn, and tested with pytest. Haystack pipelines (indexing + intake) are built in-process with CI-safe backends: mock embedder, in-memory DocumentStore, stub need decomposer, fake fleet, fake Neo4j.

Infrastructure setup, project deployment, and operate are owned by another project. This family only validates the application and produces Release artifacts those later workflows can consume.

## Goals / Non-Goals

**Goals:**

- Same GitHub Flow family as REST/portal/mobile (fast feedback / CI / release).
- Integration is the highest-priority job; later jobs `needs: [integration]`.
- Python/Haystack-appropriate toolchain: CPython 3.12 + uv + Ruff + pytest + Haystack `Pipeline` smoke.
- Semgrep-safe scripts (bind `github.*` / `inputs.*` through `env:`).
- Release artifacts are consumable by a later deploy project (wheel/sdist + image tar; GHCR off PR).

**Non-Goals:**

- Committing a Dockerfile into the application repo (Release generates one only if missing)
- Live Postgres/pgvector, Neo4j Bolt, or DigitalOcean / OpenAI LLM calls
- Prism / Mock Contract Tests (Haystack *is* the API; pytest `TestClient` covers HTTP)
- Scheduled pricing-model retrain (product OpenSpec in the application repo)
- Changing the application product `openspec/`
- Creating or changing cloud infrastructure (another project)
- Deploying the packaged service onto a runtime (another project)
- Operating the live system after go-live (another project)

## Decisions

1. **Reusable + caller gate.** Copy the REST/portal/mobile model. Each reusable file rejects any `github.workflow_ref` that is not its matching caller.
2. **Python 3.12, not 3.11 or 3.13.** Matches `.python-version` and `requires-python = ">=3.12"`.
3. **uv is the package manager.** `astral-sh/setup-uv@v5` with cache on `uv.lock`. Integration runs `uv lock --check` then `uv sync --frozen --all-groups`. Do not use pip/poetry/pdm. Do not `--extra neo4j`.
4. **Haystack smoke is the Integration resolve step.** After sync, import `haystack.Pipeline`, `create_app`, `build_indexing_pipeline`, and `build_intake_front_pipeline` with mock/memory/stub env. Analog of Gradle `:app:preBuild`.
5. **QC uses the project’s own tools.** `uv run ruff check app tests` and `uv run pytest tests/` (pytest-html already in `addopts`). No GitHub Environment / secrets — tests do not need Postgres or an LLM key.
6. **Security is Python-first.** Semgrep `p/python` (not Kotlin/Java). `uvx pip-audit` reports lockfile CVEs (does not fail the job). Trivy FS remains the CRITICAL gate. CodeQL language `python`.
7. **Release artifacts are wheel/sdist plus a Docker image.** `uv build` stages versioned + stable packages. Packaging then builds a Python 3.12 + uv + uvicorn image (app `Dockerfile` if present, else generated), saves a gzipped tar, and pushes GHCR outside pull requests. Fast Feedback and Integration CI do not request `packages: write`.
8. **Specs and YAML live under `haystack-fast-api-pipeline/`.** OpenSpec, OpenSPDD, and workflow files stay with the pipeline they describe. The application repository remains `Heavy-Rental/haystack-fast-api`.
9. **This family stops at packaging.** It does not apply IaC, create cloud resources, deploy to a runtime, or monitor production. Those concerns belong to another project. Operate is after deploy: it needs knowledge of the infrastructure and does not create it.

## Risks / Trade-offs

| Risk | Mitigation |
| --- | --- |
| `uv sync` of Haystack/ML stack is slower than Node/Maven | Cache uv on `uv.lock`; Integration timeout 30 min; Fast Feedback stays Integration-only |
| `pip-audit` on xgboost/numpy/shap will flag CVEs | Report-only; Trivy CRITICAL is the fail gate |
| `ruff format --check` would fail an unformatted tree | Lint with `ruff check` only (what `pyproject.toml` already configures) |
| Semgrep `p/python` registry drift | Same two-pass pattern as siblings (SARIF always, ERROR gate) |
| Accidental LLM spend | Never set `LLM_API_KEY`; export stub/mock env on Integration and QC |
| App has no Dockerfile | Generate a Python 3.12 + uv + uvicorn Dockerfile at packaging time (REST WAR pattern) |
| Haystack/ML image is large | Packaging timeout 30 min; cache is the runner Docker layer cache only |
| GHCR write from a PR | Push only when `github.event_name != 'pull_request'`; always upload the tar |
| Scope creep into infra / deploy / operate | OpenSpec `haystack-ci-scope` + SPDD safeguards; no Terraform/Bicep/deploy jobs in this tree |

## Migration Plan

1. Land specs + YAML in this repo under `haystack-fast-api-pipeline/`.
2. Copy the six workflow files into `Heavy-Rental/haystack-fast-api` `.github/workflows/`.
3. Require the named jobs on `develop` branch protection.
4. Archive this OpenSpec change once the install copy is accepted.

## Open Questions

None for this increment. Live pgvector/Neo4j and LLM eval gates remain deferred. Infrastructure, deploy, and operate remain another project.
