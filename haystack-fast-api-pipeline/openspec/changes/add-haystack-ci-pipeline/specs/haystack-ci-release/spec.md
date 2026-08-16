# Delta for haystack-ci-release

## Purpose

Release packaging produces versioned Python wheel and sdist artifacts with `uv build` after the quality and security gates pass, plus a Docker image tar (GHCR push off pull request). Packaging is the last job in this family. Deploying those artifacts is another project.

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
- THEN a Dockerfile is generated that installs the locked uv environment without `--extra neo4j`
- AND the default command is uvicorn serving `app.main:app` on port 8000

#### Scenario: Image tar is non-empty
- GIVEN `docker build` succeeds
- WHEN Packaging saves the image
- THEN `haystack-fast-api-v{version}-build{runNumber}-{shortSha}.tar.gz` exists and is non-empty

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
