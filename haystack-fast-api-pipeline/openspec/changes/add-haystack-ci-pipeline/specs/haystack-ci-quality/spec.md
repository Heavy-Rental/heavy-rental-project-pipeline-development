# Delta for haystack-ci-quality

## Purpose

Compile-time quality for the FastAPI + Haystack service: Ruff (the project’s Python linter) and pytest (Haystack pipeline tests, FastAPI `TestClient`, Call 1/Call 2 eval pack). No live database, Neo4j, or LLM.

## ADDED Requirements

### Requirement: Quality Control needs Integration
Quality Control SHALL run only after Integration succeeds and SHALL check out the same application source Integration resolved.

#### Scenario: Same checkout mode
- GIVEN Integration published `checkout_mode`, `app_repository`, and `app_ref`
- WHEN Quality Control starts
- THEN it checks out the application using those outputs

### Requirement: Ruff then pytest
Quality Control SHALL run `uv run ruff check app tests` and then `uv run pytest tests/`. It SHALL NOT start Postgres, Neo4j, or call an LLM. It SHALL NOT set `RUN_PGVECTOR_TESTS` or `RUN_NEO4J_TESTS`.

#### Scenario: Happy path
- GIVEN the application lints clean and its pytest suite passes
- WHEN Quality Control runs
- THEN Ruff exits 0
- AND pytest exits 0
- AND no Postgres or Neo4j container is started
- AND `LLM_API_KEY` is unset

#### Scenario: Failing unit test
- GIVEN a pytest test fails
- WHEN Quality Control runs
- THEN the job fails

#### Scenario: Ruff finding fails the job
- GIVEN Ruff reports a lint error under `app` or `tests`
- WHEN Quality Control runs
- THEN the job fails before or instead of treating the run as green

### Requirement: CI-safe Haystack backends
Quality Control SHALL export the CI-safe profile that `tests/conftest.py` already forces: stub need decomposer, mock embedder, memory DocumentStore, fake fleet, fake Neo4j, recommend graph off, no Ragas LLM transforms.

#### Scenario: No live backends
- GIVEN Quality Control starts
- WHEN pytest runs
- THEN `NEED_DECOMPOSER` is `stub`
- AND `INDEXING_EMBEDDER` is `mock`
- AND `INDEXING_DOCUMENT_STORE` is `memory`
- AND `FLEET_BACKEND` is `fake`
- AND `NEO4J_BACKEND` is `fake`

### Requirement: No secrets or Environments
Quality Control SHALL NOT require GitHub Environments or repository secrets.

#### Scenario: No database or LLM secrets
- GIVEN Quality Control starts
- WHEN the job is configured
- THEN it does not read `REST_API_DB_*`, `LLM_API_KEY`, `NEO4J_PASSWORD`, or Postgres passwords
- AND it does not set `environment:`

### Requirement: Pytest HTML report
Quality Control SHALL upload `reports/pytest-report.html` (the path configured in `pyproject.toml` `addopts`) as an artifact even when tests fail (`if: always()`).

#### Scenario: Failed tests still publish the HTML report
- GIVEN pytest fails
- WHEN the job finishes
- THEN the pytest-html artifact is still uploaded when the file exists
