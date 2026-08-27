# Delta for haystack-ci-release

## Purpose

Release packaging produces versioned Python wheel and sdist artifacts with `uv build` after Integration and Quality Control pass, plus a Docker image tar. DAST scans that image. Publish then pushes public GHCR and creates the GitHub Release. Security Testing and CodeQL stay on Integration CI. Deploying those artifacts is the Academy **CD** family in `deploy-pipeline/` (not this capability).

## ADDED Requirements

### Requirement: Packaging waits for gates
Packaging SHALL run only after Integration and Quality Control have succeeded. It SHALL NOT wait for Security Testing or CodeQL (those jobs are Integration CI only).

#### Scenario: Quality Control red blocks packaging
- GIVEN Quality Control failed
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
- AND the file copies a sanitized `haystack.prod.env` to `.env` so pydantic loads the production profile

#### Scenario: Image tar is non-empty
- GIVEN `docker build` succeeds
- WHEN Packaging saves the image
- THEN `haystack_recommender-image.tar.gz` exists and is non-empty (stable archive name; DAST/Publish consume this file, not a `{semver}` filename)

### Requirement: Image does not bake database or sync config
The Dockerfile Packaging uses SHALL NOT set `ENV`/`ARG` for `POSTGRES_*`, `SOURCE_*`, `TARGET_*`, `DATABASE_URL`, `NEED_DECOMPOSER`, `LLM_*`, `INDEXING_*`, `IDEMPOTENCY_*`, `FLEET_BACKEND`, `PRICING_SCHEMA`, `NEO4J_*`, `RECOMMEND_VIA_AGENT_GRAPH`, or `KG_*`, and SHALL NOT `COPY` a raw `.env` or `.env.prod`. `docker build` SHALL NOT pass `--build-arg` for those names. Packaging SHALL sanitize `.env.prod` (app checkout `.env.prod` or `docs/samples/.env.prod`, else generated production defaults), drop estate keys and secrets, and `COPY haystack.prod.env .env` so pydantic `Settings` loads product knobs. Packaging SHALL NOT read Haystack Environment `academy` variables or secrets. Infra `sync-secrets` (`heavy-rental/haystack`) is the Academy owner of DB/sync/`NEO4J_URI`/`NEO4J_POPULATE_URL`/`NEO4J_USER`/`NEO4J_PASSWORD` (ADR 0009). Product knobs stay injectable at runtime (process env wins over `/app/.env`).

#### Scenario: Baked ENV fails Packaging
- GIVEN the Dockerfile contains `ENV POSTGRES_HOST=…`, `ENV NEED_DECOMPOSER=stub`, or `COPY .env`
- WHEN Packaging prepares the image
- THEN the job fails before or instead of treating the image as releasable

#### Scenario: Production profile file is sanitized into the image
- GIVEN the app checkout has `.env.prod` (or Packaging generated production defaults)
- WHEN Packaging prepares the image
- THEN `haystack.prod.env` has no `POSTGRES_*`, `DATABASE_URL`, `NEO4J_URI`, `NEO4J_PASSWORD`, or `LLM_API_KEY`
- AND the Dockerfile contains `COPY haystack.prod.env .env`
- AND `/app/.env` is present after `docker build`

#### Scenario: Academy Environment is not read at Packaging
- GIVEN Haystack Environment `academy` has `NEED_DECOMPOSER=llm`
- WHEN Packaging builds the image
- THEN the image `/app/.env` is produced only from the app `.env.prod` (or generated defaults)
- AND Packaging does not consult Environment `academy` variables or secrets

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
- AND `Settings().app_env` is loaded from `/app/.env`
- AND `docker run -e APP_ENV=ci-override` makes `Settings().app_env` equal `ci-override`

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

### Requirement: DAST scans the packaged image
DAST SHALL run after Packaging succeeds. It SHALL start the packaged image and run OWASP ZAP, Dastardly, and Nuclei. It SHALL upload `dast-reports/` including `combined-dast-report.pdf` (artifact `dast-combined-report-pdf`).

#### Scenario: DAST needs Packaging
- GIVEN Packaging failed
- WHEN DAST is evaluated
- THEN DAST does not start

### Requirement: Publish pushes GHCR and creates the GitHub Release
Publish SHALL run after Packaging and DAST succeed. It SHALL push the image to `ghcr.io/<owner>/haystack_recommender` tagged with a new `x.y.z` semver and `:latest`. The semver SHALL be the highest existing `x.y.z` tag on that GHCR package with the patch incremented; if no such tag exists, it SHALL be `1.0.0`. Publish SHALL NOT overwrite an existing `x.y.z` tag. Publish SHALL create a GitHub Release on `master` (`gh release create`). The Release caller SHALL NOT subscribe to `release` or `pull_request` events. Packaging SHALL upload the gzipped image tar and SHALL NOT `docker push`.

#### Scenario: workflow_dispatch publishes
- GIVEN a `workflow_dispatch` triggered the release pipeline
- AND DAST succeeded
- AND the highest GHCR `haystack_recommender` semver tag is `1.0.1` or none exist
- WHEN Publish runs
- THEN `docker push` runs for `ghcr.io/<owner>/haystack_recommender:1.0.2` (or `1.0.0` when none exist) and `:latest`
- AND `gh release create` runs targeting `master`

#### Scenario: Packaging does not push
- GIVEN Packaging finished the Docker build
- WHEN Packaging completes
- THEN no `docker push` runs in Packaging
- AND the gzipped image tar is still uploaded for DAST and Publish
