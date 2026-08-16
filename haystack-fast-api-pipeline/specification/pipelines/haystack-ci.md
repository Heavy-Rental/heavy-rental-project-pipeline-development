# Haystack FastAPI CI family

**Application:** https://github.com/Heavy-Rental/haystack-fast-api  
**Authoring tree:** `haystack-fast-api-pipeline/` in this pipeline-development repo  
**Stack:** Python 3.12 / uv / FastAPI / Haystack 2.x / Ruff / pytest

This family validates and packages the service. It does not create infrastructure, deploy the service, or operate production. Those belong to another project.

## GitHub Flow

```
feature branch push  →  Fast Feedback (Integration only)
PR / push → develop  →  Integration CI (full gates, no packaging)
develop → master PR or published GitHub Release
                     →  Release (full gates + uv build wheel/sdist + Docker)
```

## Job graph (Integration CI)

```
assert-caller
      │
      ▼
 Integration          CPython 3.12 + uv lock --check + uv sync --frozen
                      + Haystack Pipeline / FastAPI create_app smoke
      │
      ├── Quality Control     ruff check + pytest tests/ (CI-safe backends)
      ├── Security Testing    Semgrep p/python + pip-audit report + Trivy
      └── CodeQL Analysis     python / security-and-quality
      │
      ▼
 GitHub Flow CI Gate
```

Release adds **Packaging** (`uv build` wheel + sdist, then Docker image tar + GHCR push off PR) after Integration + QC + Security + CodeQL. Packaging is the last job in this family. A later project may consume the artifacts to deploy.

## Python / Haystack tools (not Java / Android / Node)

| Concern | Tool |
| --- | --- |
| Interpreter | CPython 3.12 (`actions/setup-python`) |
| Lock + install | uv (`astral-sh/setup-uv`, `uv.lock`) |
| Integration smoke | `haystack.Pipeline`, `create_app`, `build_indexing_pipeline`, `build_intake_front_pipeline` |
| Lint | Ruff (`uv run ruff check app tests`) |
| Tests | pytest + pytest-html (`uv run pytest tests/`) |
| Python SAST | Semgrep `p/python` |
| Python SCA report | `uvx pip-audit` on `uv export` |
| FS / CRITICAL SCA | Trivy |
| Code scanning | CodeQL `python` |
| Package | `uv build` (Hatchling wheel + sdist) |
| Image | `docker build` (app Dockerfile or generated uv/uvicorn) → gzipped tar; GHCR off PR |

CI-safe Haystack profile (matches `tests/conftest.py` and `QUICKSTART.md` Profile A):

`NEED_DECOMPOSER=stub`, `INDEXING_EMBEDDER=mock`, `INDEXING_DOCUMENT_STORE=memory`, `FLEET_BACKEND=fake`, `NEO4J_BACKEND=fake`, `RECOMMEND_VIA_AGENT_GRAPH=false`, `KG_APPLY_TRANSFORMS=false`. No `LLM_API_KEY`.

## Branch protection (application repo `develop`)

Require these check names:

1. Integration *(highest priority)*
2. Quality Control
3. Security Testing
4. CodeQL Analysis
5. GitHub Flow CI Gate

## Local validation (this repo)

```bash
actionlint haystack-fast-api-pipeline/fast-feedback-ci-pipeline/fast-feedback-pipeline.yml
actionlint haystack-fast-api-pipeline/fast-feedback-ci-pipeline/haystack-fast-feedback-caller.yml
actionlint haystack-fast-api-pipeline/integration-pipeline/integration-pipeline.yml
actionlint haystack-fast-api-pipeline/integration-pipeline/haystack-ci-caller.yml
actionlint haystack-fast-api-pipeline/release-pipeline/release-pipeline.yml
actionlint haystack-fast-api-pipeline/release-pipeline/haystack-release-caller.yml

# Local act smoke (caller gate). See haystack-fast-api-pipeline/act/README.md
./haystack-fast-api-pipeline/act/run-act.sh smoke
```

## Install into the application repo

Copy each pair into `Heavy-Rental/haystack-fast-api`:

```
.github/workflows/haystack-fast-feedback-caller.yml
.github/workflows/fast-feedback-pipeline.yml
.github/workflows/haystack-ci-caller.yml
.github/workflows/integration-pipeline.yml
.github/workflows/haystack-release-caller.yml
.github/workflows/release-pipeline.yml
```

No repository secrets are required for v1.

## Pipeline boundaries

| Concern | In this family? |
| --- | --- |
| Fast Feedback, Integration CI, Release packaging | Yes |
| Live pgvector, Neo4j, LLM calls, Prism mocks | No |
| Scheduled model retrain | No (product OpenSpec in the application repo) |
| Committing a Dockerfile to the application repo | No (Release generates one only if the checkout has none) |
| Create or change infrastructure | No — another project |
| Deploy the packaged service | No — another project (consumes wheel / image tar / GHCR) |
| Operate the live system | No — another project (after go-live) |

Operate requires knowledge of the running platform. It does not create that platform. This family does not provision cloud resources or apply IaC.
