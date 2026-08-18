# Delta for rest-ci-release

## Purpose

Release packaging produces a versioned WAR and a Tomcat Docker image after the quality and security gates pass. Deploying those artifacts is the Academy CD family, not this capability.

## ADDED Requirements

### Requirement: Packaging waits for gates
Packaging SHALL run only after Integration, Quality Control, Security Testing, and CodeQL have succeeded.

#### Scenario: Security red blocks packaging
- GIVEN Security Testing failed
- WHEN Packaging is evaluated
- THEN Packaging does not start

### Requirement: Versioned WAR
Packaging SHALL run `./mvnw -DskipTests package` and SHALL stage a `.war` that contains `WEB-INF/` as versioned and stable filenames. The job SHALL fail if no `.war` exists, if `packaging` is not `war`, or if the file is an executable JAR.

#### Scenario: Both names uploaded
- GIVEN package produced a WAR with `WEB-INF/`
- WHEN Packaging finishes
- THEN a versioned WAR and a stable WAR copy are uploaded as artifacts
- AND both files are non-empty

#### Scenario: JAR is rejected
- GIVEN `target/` has only an executable `.jar`
- WHEN Packaging verifies the package
- THEN the job fails
- AND no image is built from that JAR as `ROOT.war`

### Requirement: WAR includes Spring prod properties
The packaged WAR SHALL contain `WEB-INF/classes/application-prod.properties` (hyphen). Packaging SHALL fail if that file is missing. If the WAR only contains `application.prod.properties` (dot), Packaging SHALL fail and tell the operator to use the hyphen name.

#### Scenario: Hyphen file present
- GIVEN `mvn package` produced a WAR
- WHEN Packaging inspects the WAR
- THEN `WEB-INF/classes/application-prod.properties` exists

### Requirement: Tomcat image
Packaging SHALL always generate and build an image from `tomcat:10.1-jdk21-temurin` with the WAR as `ROOT.war`, `EXPOSE 8080`, and `ENV SPRING_PROFILES_ACTIVE=prod`. It SHALL NOT use an application `Dockerfile` as the GHCR / Docker Desktop / compose image. It SHALL save a gzipped tar that includes the local, `:latest`, and both GHCR tags.

#### Scenario: App Dockerfile is not the deploy image
- GIVEN the Spring repo contains a `Dockerfile`
- WHEN Packaging prepares the image
- THEN that file is moved aside
- AND the generated Tomcat + `ROOT.war` Dockerfile is used for `docker build`

#### Scenario: Image tar is non-empty
- GIVEN `docker build` succeeds
- WHEN Packaging saves the image
- THEN a gzipped tar artifact exists and is non-empty

### Requirement: GHCR push only off pull requests
Packaging SHALL push the image to `ghcr.io/<owner>/heavy_rental_rest_api` tagged with a new `x.y.z` semver and `:latest` when the event is not a pull request. The semver SHALL be the highest existing `x.y.z` tag on that GHCR package with the patch incremented; if no such tag exists, it SHALL be `1.0.0`. Packaging SHALL NOT overwrite an existing `x.y.z` tag. On a `develop` → `master` pull request, Packaging SHALL skip the push and still upload the image tar.

#### Scenario: Published release pushes
- GIVEN a published GitHub Release triggered the release pipeline
- AND the highest GHCR `heavy_rental_rest_api` semver tag is `1.0.1` or none exist
- WHEN Packaging finishes the Docker build
- THEN `docker push` runs for `ghcr.io/<owner>/heavy_rental_rest_api:1.0.2` (or `1.0.0` when none exist) and `:latest`

#### Scenario: PR skips registry push
- GIVEN a pull request from `develop` to `master` triggered the release pipeline
- WHEN Packaging finishes the Docker build
- THEN no `docker push` runs
- AND the gzipped image tar is still uploaded

### Requirement: Cloud JDBC artifact has no password
Packaging SHALL upload a datasource env file whose `SPRING_DATASOURCE_URL` uses `REST_API_CLOUD_DB_HOST` and SHALL NOT write `SPRING_DATASOURCE_PASSWORD` into that artifact. That file SHALL NOT be copied into the Docker image.

#### Scenario: Password omitted
- GIVEN Packaging builds the deploy env file
- WHEN the artifact is written
- THEN it contains `SPRING_DATASOURCE_URL`
- AND it does not contain the cloud database password

#### Scenario: Artifact stays out of the image
- GIVEN the generated or application Dockerfile
- WHEN Packaging prepares the image
- THEN the Dockerfile does not `COPY` `spring-datasource.env` or any `*.env`

### Requirement: Image does not bake guest or CI database config
The Dockerfile Packaging uses SHALL NOT set `ENV`/`ARG` for `POSTGRES_*`, `SPRING_DATASOURCE_*`, `SPRING_JPA_*`, `HAYSTACK_*`, `STRIPE_*`, `APP_JWT_*`, `REST_API_CLOUD_DB_*`, or `REST_API_DB_*`. It MAY set `ENV SPRING_PROFILES_ACTIVE=prod`. `docker build` SHALL NOT pass `--build-arg` for secret names. If `src/main/resources/application-prod.properties` exists, Packaging SHALL fail when that file contains Stripe `sk_` / `whsec_`, the default JWT string, a baked JDBC URL, or a secret assignment without a `${ENV}` placeholder.

#### Scenario: Baked ENV fails Packaging
- GIVEN the Dockerfile contains `ENV SPRING_DATASOURCE_URL=…` or `COPY .env`
- WHEN Packaging prepares the image
- THEN the job fails before treating the image as releasable

### Requirement: Runtime env is visible without a live database
After a successful build, Packaging SHALL inspect image `Config.Env` and SHALL run the image with dummy `SPRING_DATASOURCE_URL`, `POSTGRES_HOST`, `HAYSTACK_BASE_URL`, `STRIPE_PUBLISHABLE_KEY`, and `APP_JWT_SECRET`. Those dummy values SHALL be visible inside the container. Packaging SHALL NOT connect to Academy RDS or QC Postgres.

#### Scenario: Dummy guest keys are visible
- GIVEN the image built
- WHEN Packaging runs the container with `POSTGRES_HOST=sor.example.test` and `HAYSTACK_BASE_URL=http://haystack.example.test:8000`
- THEN those values appear in the container environment
- AND `Config.Env` does not contain baked `POSTGRES_*` / `SPRING_DATASOURCE_*` / `HAYSTACK_*` / `STRIPE_*` / `APP_JWT_*`

### Requirement: Image is deployable on any Docker Engine
After `docker build`, Packaging SHALL confirm the image exposes `8080/tcp`, SHALL confirm `/usr/local/tomcat/webapps/ROOT.war` exists and contains `WEB-INF/`, SHALL start Tomcat with dummy env, SHALL wait until TCP `:8080` accepts, and SHALL stop the container. Packaging SHALL NOT leave Tomcat running and SHALL NOT require actuator HTTP 200 (that needs a live database).

#### Scenario: Tomcat binds 8080
- GIVEN the image built
- WHEN Packaging starts the container
- THEN TCP `:8080` accepts
- AND `ROOT.war` is a webapp with `WEB-INF/`
- AND the container is removed before Packaging finishes
