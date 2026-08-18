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
Packaging SHALL build a Docker image after staging wheel/sdist artifacts and SHALL do so before uploading those packages. If the application checkout has no `Dockerfile`, Packaging SHALL generate a Python 3.12 + uv + uvicorn Dockerfile. The image SHALL NOT start Postgres, Neo4j, or call an LLM during the build.

#### Scenario: App Dockerfile used when present
- GIVEN the application contains a `Dockerfile`
- WHEN Packaging prepares the image
- THEN that file is used as the build context Dockerfile

#### Scenario: Generated uvicorn Dockerfile when missing
- GIVEN the application has no `Dockerfile`
- WHEN Packaging prepares the image
- THEN a Dockerfile is generated that installs the locked uv environment with `--extra neo4j`
- AND the default command is uvicorn serving `app.main:app` on port 8000
- AND the file does not set `ENV` or `ARG` for `POSTGRES_*`, `SOURCE_*`, `TARGET_*`, `DATABASE_URL`, `NEO4J_PASSWORD`, or `LLM_API_KEY`

#### Scenario: Image tar is non-empty
- GIVEN `docker build` succeeds
- WHEN Packaging saves the image
- THEN `haystack-fast-api-v{version}-build{runNumber}-{shortSha}.tar.gz` exists and is non-empty

### Requirement: Image does not bake database or sync config
The Dockerfile Packaging uses (generated or from the application) SHALL NOT set `ENV`/`ARG` for `POSTGRES_*`, `SOURCE_*`, `TARGET_*`, `DATABASE_URL`, `NEO4J_PASSWORD`, or `LLM_API_KEY`, and SHALL NOT `COPY` a `.env` file. `docker build` SHALL NOT pass `--build-arg` for those names.

#### Scenario: Baked ENV fails Packaging
- GIVEN the Dockerfile contains `ENV POSTGRES_HOST=…` or `COPY .env`
- WHEN Packaging prepares the image
- THEN the job fails before or instead of treating the image as releasable

### Requirement: Runtime env is visible without a live database
After a successful build, Packaging SHALL inspect the image `Config.Env` and SHALL run the image with dummy `SOURCE_*`, `TARGET_*`, `POSTGRES_USERNAME` / `POSTGRES_PASSWORD`, and `DATABASE_URL`. Those dummy values SHALL be visible inside the container. Packaging SHALL NOT start Postgres, SHALL NOT connect to Academy RDS, and SHALL NOT run `postgres-haystack-sync` against a network.

#### Scenario: Dummy SOURCE and TARGET are visible
- GIVEN the image built
- WHEN Packaging runs the container with `SOURCE_HOST=sor.example.test` and `TARGET_HOST=haystack.example.test`
- THEN those values appear in the container environment
- AND `Config.Env` does not contain baked `SOURCE_*` / `TARGET_*` / `POSTGRES_*`

### Requirement: Sidecar packages copied only when present
When Packaging generates a Dockerfile, it SHALL `COPY postgres_haystack_sync` and `COPY neo4j_populate` only if those directories exist next to `app/` in the checkout. It SHALL NOT invent those packages. Missing `import postgres_haystack_sync` SHALL warn and SHALL NOT fail Packaging.

#### Scenario: No sidecar directory
- GIVEN the application checkout has `app/` and no `postgres_haystack_sync/`
- WHEN Packaging generates the Dockerfile
- THEN the Dockerfile copies `app/`
- AND it does not `COPY postgres_haystack_sync`

### Requirement: GHCR push only off pull requests
Packaging SHALL push the image to `ghcr.io` tagged with the versioned tag and `:latest` when the event is not a pull request. On a `develop` → `master` pull request, Packaging SHALL skip the push and still upload the image tar.

#### Scenario: Published release pushes
- GIVEN a published GitHub Release triggered the release pipeline
- WHEN Packaging finishes the Docker build
- THEN `docker push` runs for the versioned GHCR tag and `:latest`

#### Scenario: PR skips registry push
- GIVEN a pull request from `develop` to `master` triggered the release pipeline
- WHEN Packaging finishes the Docker build
- THEN no `docker push` runs
- AND the gzipped image tar is still uploaded
