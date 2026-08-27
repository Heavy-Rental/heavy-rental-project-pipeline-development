# Haystack FastAPI CI family

**Application:** https://github.com/Heavy-Rental/haystack-fast-api  
**Authoring tree:** `haystack-fast-api-pipeline/` in this pipeline-development repo  
**Stack:** Python 3.12 / uv / FastAPI / Haystack 2.x / Ruff / pytest

This family validates and packages the service. It does not create infrastructure or operate production. Academy and paid **app CD** (compose onto `asg-haystack`) is a separate family: [`haystack-cd.md`](haystack-cd.md).

## GitHub Flow

```
feature branch push  →  Fast Feedback (Integration only; sole Integration-stage run for that SHA)
PR / push → develop  →  Integration CI (Integration reuses Fast Feedback on PR; full gates; SAST here)
workflow_dispatch     →  Release (master + QC + image + DAST + public GHCR + GitHub Release)
```

## Job graph (Integration CI)

```
assert-caller
      │
      ▼
 Integration          PR: reuse Fast Feedback for the head SHA (skip uv/layout)
                      else: CPython 3.12 + uv lock --check + uv sync --frozen
                      + Haystack Pipeline / FastAPI create_app smoke
                      job id integration (Haystack has no environment: integration)
      │
      ├── Quality Control     ruff check + pytest tests/ (CI-safe backends)
      ├── Security Testing    Semgrep app + GHA + pip-audit report + Trivy
      └── CodeQL Analysis     python / security-and-quality
      │
      ▼
 GitHub Flow CI Gate
```

Do **not** `uses:` `fast-feedback-pipeline.yml` from `haystack-ci-caller.yml`. Copy both Integration files into the Haystack app repo and call `./.github/workflows/integration-pipeline.yml`.

Release (`workflow_dispatch` of **Haystack Release Pipeline Invoke**) does **not** re-run Security Testing or CodeQL. Those stay on Integration CI. Release job graph:

```
assert-caller
      │
      ▼
 Integration          CPython 3.12 + uv; checkout master
      │
      ▼
 Quality Control      ruff check + pytest tests/
      │
      ▼
 Packaging            uv build + generated uvicorn image tar (no docker push)
      │
      ▼
 DAST                 ZAP + Dastardly + Nuclei against the image
      │
      ▼
 Publish              public GHCR haystack_recommender:<semver> + :latest
                      + GitHub Release on master
```

Academy CD consumes a public GHCR/ECR tag or the tar. The image must accept infra `heavy-rental/haystack` keys and Profile knobs at runtime (ADR 0008 / 0009). Packaging sanitizes `.env.prod` into `/app/.env` (product knobs only), proves dummy `-e` injection (process env wins), and `GET /docs` or `/health` on `:8000` (no live Postgres). **CD / ALB `tg-haystack`** waits for `GET :8000/health` **2xx** only. Packaging does **not** read Environment `academy`; those vars overlay guest `.env` at CD time only. Packaging does **not** `docker push`; Publish does that after DAST.

## Python / Haystack tools (not Java / Android / Node)

| Concern | Tool |
| --- | --- |
| Interpreter | CPython 3.12 (`actions/setup-python`) |
| Lock + install | uv (`astral-sh/setup-uv`, `uv.lock`) |
| Integration smoke | `haystack.Pipeline`, `create_app`, `build_indexing_pipeline`, `build_intake_front_pipeline` |
| Lint | Ruff (`uv run ruff check app tests`) |
| Tests | pytest + pytest-html (`uv run pytest tests/`) |
| Python SAST | Two Semgrep passes. App: `p/python` `p/fastapi` + OWASP / audit / secrets / CWE Top 25 / Gitleaks / SQL injection / JWT / insecure-transport, plus custom ERROR rules for plaintext credentials in `.env`/YAML and Python assignments; excludes `.github/**`. GHA: `p/github-actions` plus custom inherit / hardcoded-secret rules (`secrets: inherit` ERROR except paid CD caller; explicit secrets-context maps allowed; `persist-credentials` is not a finding). Reports: `semgrep.sarif` + `semgrep-gha.sarif` (all severities); gate is ERROR-only |
| Python SCA report | `uvx pip-audit` on `uv export` |
| FS / CRITICAL SCA | Trivy |
| Human security report | Combined PDF artifact `security-combined-report-pdf` (SARIF + pip-audit); download from the PR Checks tab (workflow Summary → Artifacts, or Security Testing job summary) |
| Human DAST report | Combined PDF artifact `dast-combined-report-pdf` (`dast-reports/combined-dast-report.pdf`); download from the Release run Summary → Artifacts, the DAST job summary link, or the GitHub Release |
| Code scanning | CodeQL `python` |
| Package | `uv build` (Hatchling wheel + sdist) |
| Image | Always-generated `python:3.12-slim-bookworm` + uv + `uvicorn app.main:app :8000` (app Dockerfile ignored). Publish pushes GHCR `haystack_recommender:<semver>` + `:latest` (semver is previous GHCR `x.y.z` + patch, or `1.0.0`) and creates the GitHub Release. No baked infra `ENV`/`ARG`. Sanitized `.env.prod` → `/app/.env` for pydantic product knobs (`APP_ENV=prod`, …). Estate keys stay out of that file. Packaging proves dummy `docker run -e` env (overrides the file) and `GET /docs` or `GET /health` on `:8000`. Sidecar dirs copied only if present. |

CI-safe Haystack profile (matches `tests/conftest.py` and `QUICKSTART.md` Profile A):

`NEED_DECOMPOSER=stub`, `INDEXING_EMBEDDER=mock`, `INDEXING_DOCUMENT_STORE=memory`, `FLEET_BACKEND=fake`, `NEO4J_BACKEND=fake`, `RECOMMEND_VIA_AGENT_GRAPH=false`, `KG_APPLY_TRANSFORMS=false`. No `LLM_API_KEY`.

No GitHub Environment or repository secrets are required for v1 CI.

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

`DEFAULT_APP_REPOSITORY` in the reusable YAML is `Heavy-Rental/haystack-fast-api`. When the caller runs **in** the app repo, checkout is the calling repo (into `app/`).

## Pipeline boundaries

| Concern | In this CI family? |
| --- | --- |
| Fast Feedback, Integration CI, Release packaging | Yes |
| Live pgvector, Neo4j, LLM calls, Prism mocks | No |
| Scheduled model retrain | No (product OpenSpec in the application repo) |
| Committing a Dockerfile to the application repo | No (Release always generates uvicorn; app Dockerfile is not the deploy image) |
| Create or change infrastructure | No — infra project |
| Deploy the packaged service | No — Academy CD family ([`haystack-cd.md`](haystack-cd.md)) |
| Operate the live system | No — infra project (after go-live) |

Operate requires knowledge of the running platform. It does not create that platform. This CI family does not provision cloud resources or apply IaC.
