# Delta for haystack-ci-integration

## Purpose

Highest-priority gate: fetch the FastAPI + Haystack application, install CPython 3.12 and uv, sync the locked environment, and prove the project layout plus Haystack pipeline imports.

On Integration CI the job id is `integration` and the check name is **Integration** (Haystack has no `environment: integration`). Fast Feedback and Release keep the same job id and name. On `pull_request`, uv/layout SHALL be skipped when Fast Feedback already succeeded for the PR head SHA.

## ADDED Requirements

### Requirement: Integration is first
The Integration job SHALL run only after the caller gate succeeds. Quality Control, Security Testing, CodeQL, and Packaging SHALL declare a dependency on Integration when those jobs exist in the workflow.

#### Scenario: Failed Integration blocks later jobs
- GIVEN Integration fails
- WHEN the workflow continues
- THEN Quality Control, Security Testing, CodeQL, and Packaging (when present) do not start
- AND the GitHub Flow CI Gate (when present) still runs and fails

### Requirement: CPython 3.12
Integration SHALL install CPython 3.12 and SHALL use that interpreter for uv and subsequent Python commands.

#### Scenario: Toolchain version
- GIVEN Integration has checked out the application
- WHEN Python is set up
- THEN the runner Python version is 3.12

### Requirement: uv is mandatory
When uv/layout run, Integration SHALL install uv, fail if `uv.lock` is missing, and SHALL run `uv lock --check` then `uv sync --frozen --all-groups`. It SHALL NOT invoke pip, poetry, or pdm to install the application. It SHALL NOT pass `--extra neo4j`. On Integration CI `pull_request`, those uv/layout steps SHALL be skipped when Fast Feedback already succeeded for the PR head SHA.

#### Scenario: Lock present and frozen sync
- GIVEN the application contains `uv.lock` and `pyproject.toml`
- AND uv/layout are not skipped
- WHEN Integration prepares the environment
- THEN `uv lock --check` succeeds
- AND `uv sync --frozen --all-groups` succeeds
- AND `--extra neo4j` is not used

#### Scenario: Lock missing
- GIVEN the application does not contain `uv.lock`
- AND uv/layout are not skipped
- WHEN Integration prepares the environment
- THEN the job fails with an error that `uv.lock` is required

#### Scenario: PR skips uv when Fast Feedback succeeded
- GIVEN Integration on a pull_request
- AND Fast Feedback succeeded for the PR head SHA
- WHEN Integration continues
- THEN uv lock/sync and Haystack/layout smoke are skipped
- AND the job still succeeds

### Requirement: Project layout
Integration SHALL verify the application root contains `pyproject.toml`, `uv.lock`, `.python-version`, `app/main.py`, and `tests/conftest.py`.

#### Scenario: Required files present
- GIVEN a checkout of Heavy Rental haystack-fast-api
- AND uv/layout are not skipped
- WHEN layout checks run
- THEN each required path exists
- AND the job succeeds

#### Scenario: Required file missing
- GIVEN any required path is absent
- AND uv/layout are not skipped
- WHEN layout checks run
- THEN the job fails

### Requirement: Haystack and FastAPI smoke
After a successful sync, Integration SHALL import Haystack, construct the FastAPI app factory, and construct the indexing and intake Haystack pipelines using CI-safe backends (mock embedder, memory DocumentStore, stub decomposer, fake fleet, fake Neo4j).

#### Scenario: Pipelines construct without live backends
- GIVEN `uv sync` succeeded
- WHEN the Haystack smoke runs
- THEN `haystack.Pipeline` imports
- AND `app.main.create_app` returns a FastAPI app
- AND `build_indexing_pipeline` and `build_intake_front_pipeline` return without calling an LLM, Postgres, or Neo4j
- AND `LLM_API_KEY` is unset

### Requirement: uv cache and lock fingerprint
Integration SHALL cache uv downloads via the uv setup action keyed on `uv.lock` and SHALL upload `uv.lock` (and `pyproject.toml`) as a short-lived fingerprint artifact.

#### Scenario: Fingerprint artifact
- GIVEN layout checks passed
- WHEN Integration finishes
- THEN an artifact containing `uv.lock` is uploaded
