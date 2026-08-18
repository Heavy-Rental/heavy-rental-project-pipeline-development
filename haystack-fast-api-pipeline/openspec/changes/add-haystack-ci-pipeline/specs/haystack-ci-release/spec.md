# Delta for haystack-ci-release

## Purpose

Release packaging produces versioned Python wheel and sdist artifacts with `uv build` after the quality and security gates pass, plus a Docker image tar (GHCR push off pull request). Packaging is the last job in this **CI** family. Deploying those artifacts is the Academy **CD** family in `deploy-pipeline/` (not this capability).

## ADDED Requirements

### Requirement: Packaging waits for gates
Packaging SHALL run only after Integration, Quality Control, Security Testing, and CodeQL have succeeded.

#### Scenario: Security red blocks packaging
- GIVEN Security Testing failed
- WHEN Packaging is evaluated
- THEN Packaging does not start

### Requirement: uv build
Packaging SHALL run `uv build` and SHALL NOT require GitHub Environment secrets.

#### Scenario: Wheel and sdist
- GIVEN Quality Control already passed
- WHEN Packaging runs `uv build`
- THEN `dist/` contains at least one `.whl` and one `.tar.gz`
- AND the job fails if `dist/` is empty

### Requirement: Versioned and stable artifact names
Packaging SHALL copy the wheel to a versioned name `haystack-fast-api-v{version}-build{runNumber}-{shortSha}.whl` and a stable name `haystack-fast-api.whl`, do the same for the sdist (`.tar.gz`), and SHALL upload all staged files.

#### Scenario: Both names uploaded
- GIVEN `uv build` produced a wheel and an sdist
- WHEN Packaging finishes
- THEN both the versioned and stable wheel files are uploaded as artifacts
- AND both files are non-empty

### Requirement: Docker image before package upload
Packaging SHALL build a Docker image after staging wheel/sdist artifacts and SHALL do so before uploading those packages. Packaging SHALL always generate a Python 3.12 + uv + uvicorn Dockerfile (`app.main:app` on port 8000) and SHALL NOT use an application `Dockerfile` as the GHCR / Docker Desktop / compose image. The image SHALL NOT start Postgres, Neo4j, or call an LLM during the build.

#### Scenario: App Dockerfile is not the deploy image
- GIVEN the application contains a `Dockerfile`
- WHEN Packaging prepares the image
- THEN that file is moved aside
- AND the generated uvicorn Dockerfile is used for `docker build`

#### Scenario: Generated uvicorn Dockerfile
- GIVEN Packaging prepares the image
- WHEN the Dockerfile is generated
- THEN it installs the locked uv environment with `--extra neo4j`
- AND the default command is uvicorn serving `app.main:app` on port 8000
- AND the file does not set `ENV` or `ARG` for infra SM keys or Profile knobs (`POSTGRES_*`, `NEED_DECOMPOSER`, `LLM_*`, `INDEXING_*`, `NEO4J_*`, …)

#### Scenario: Image tar is non-empty
- GIVEN `docker build` succeeds
- WHEN Packaging saves the image
- THEN `haystack_recommender-{semver}.tar.gz` exists and is non-empty

### Requirement: Image does not bake database or sync config
The Dockerfile Packaging uses SHALL NOT set `ENV`/`ARG` for `POSTGRES_*`, `SOURCE_*`, `TARGET_*`, `DATABASE_URL`, `NEED_DECOMPOSER`, `LLM_*`, `INDEXING_*`, `IDEMPOTENCY_*`, `FLEET_BACKEND`, `PRICING_SCHEMA`, `NEO4J_*`, `RECOMMEND_VIA_AGENT_GRAPH`, or `KG_*`, and SHALL NOT `COPY` a `.env` file. `docker build` SHALL NOT pass `--build-arg` for those names. Infra `sync-secrets` (`heavy-rental/haystack`) is the Academy owner of DB/sync/`FLEET_BACKEND`/`NEO4J_URI`/`NEO4J_POPULATE_URL`/`NEO4J_USER`/`NEO4J_PASSWORD` (ADR 0009). Product knobs stay injectable at runtime.

#### Scenario: Baked ENV fails Packaging
- GIVEN the Dockerfile contains `ENV POSTGRES_HOST=…`, `ENV NEED_DECOMPOSER=stub`, or `COPY .env`
- WHEN Packaging prepares the image
- THEN the job fails before or instead of treating the image as releasable

### Requirement: Runtime env is visible without a live database
After a successful build, Packaging SHALL inspect the image `Config.Env` and SHALL run the image with dummy values for infra `heavy-rental/haystack` keys (`SOURCE_*`, `TARGET_*`, `POSTGRES_*`, `DATABASE_URL`, `FLEET_BACKEND`, `NEO4J_*`, `LLM_API_KEY`) and for the remaining `.env.example` knobs (`NEED_DECOMPOSER`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_TIMEOUT_SECONDS`, `LLM_TEMPERATURE`, `INDEXING_*`, `IDEMPOTENCY_TTL_SECONDS`, `INDEXING_VIA_AGENT_GATE`, `PRICING_SCHEMA`, `RECOMMEND_VIA_AGENT_GRAPH`, `KG_ARTIFACT_DIR`, `KG_APPLY_TRANSFORMS`). Those dummy values SHALL be visible inside the container. Packaging SHALL NOT start Postgres, SHALL NOT connect to Academy RDS, and SHALL NOT call an LLM.

#### Scenario: Dummy SOURCE and TARGET are visible
- GIVEN the image built
- WHEN Packaging runs the container with `SOURCE_HOST=sor.example.test` and `TARGET_HOST=haystack.example.test`
- THEN those values appear in the container environment
- AND `Config.Env` does not contain baked `SOURCE_*` / `TARGET_*` / `POSTGRES_*`

#### Scenario: Profile knobs are injectable
- GIVEN the image built
- WHEN Packaging runs the container with dummy `NEED_DECOMPOSER`, `LLM_*`, `INDEXING_*`, `FLEET_BACKEND`, `NEO4J_*`, and `KG_*`
- THEN those values appear in the container environment
- AND `Config.Env` does not contain baked `NEED_DECOMPOSER` / `LLM_*` / `INDEXING_*` / `FLEET_BACKEND` / `NEO4J_*` / `KG_*`

### Requirement: Image is deployable and endpoints are reachable
After `docker build`, Packaging SHALL confirm the image exposes `8000/tcp`, SHALL confirm `/app/app/main.py` exists, SHALL start the default uvicorn command with dummy DB/sync env and CI-safe Haystack flags (not baked into the image), SHALL wait until `GET /docs` or `GET /health` on port 8000 returns HTTP 200–302, and SHALL stop the container. Packaging SHALL NOT leave uvicorn running and SHALL NOT require a live Postgres (`/health` may be `degraded`).

#### Scenario: uvicorn serves FastAPI endpoints
- GIVEN the image built
- WHEN Packaging starts the container
- THEN `GET /docs` or `GET /health` on port 8000 returns 200–302
- AND the container is removed before Packaging finishes

### Requirement: Sidecar packages copied only when present
When Packaging generates a Dockerfile, it SHALL `COPY postgres_haystack_sync` and `COPY neo4j_populate` only if those directories exist next to `app/` in the checkout. It SHALL NOT invent those packages. Missing `import postgres_haystack_sync` SHALL warn and SHALL NOT fail Packaging.

#### Scenario: No sidecar directory
- GIVEN the application checkout has `app/` and no `postgres_haystack_sync/`
- WHEN Packaging generates the Dockerfile
- THEN the Dockerfile copies `app/`
- AND it does not `COPY postgres_haystack_sync`

### Requirement: GHCR push only off pull requests
Packaging SHALL push the image to `ghcr.io/<owner>/haystack_recommender` tagged with a new `x.y.z` semver and `:latest` when the event is not a pull request. The semver SHALL be the highest existing `x.y.z` tag on that GHCR package with the patch incremented; if no such tag exists, it SHALL be `1.0.0`. Packaging SHALL NOT overwrite an existing `x.y.z` tag. On a `develop` → `master` pull request, Packaging SHALL skip the push and still upload the image tar.

#### Scenario: Published release pushes
- GIVEN a published GitHub Release triggered the release pipeline
- AND the highest GHCR `haystack_recommender` semver tag is `1.0.1` or none exist
- WHEN Packaging finishes the Docker build
- THEN `docker push` runs for `ghcr.io/<owner>/haystack_recommender:1.0.2` (or `1.0.0` when none exist) and `:latest`

#### Scenario: PR skips registry push
- GIVEN a pull request from `develop` to `master` triggered the release pipeline
- WHEN Packaging finishes the Docker build
- THEN no `docker push` runs
- AND the gzipped image tar is still uploaded
