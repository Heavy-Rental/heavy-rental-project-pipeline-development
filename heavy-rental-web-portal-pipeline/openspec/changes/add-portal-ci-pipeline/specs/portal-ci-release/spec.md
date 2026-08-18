# Delta for portal-ci-release

## Purpose

Release packaging produces a Vite `dist/` zip and an nginx Docker image after the quality and security gates pass.

## ADDED Requirements

### Requirement: Packaging waits for gates
Packaging SHALL run only after Integration, Quality Control, Security Testing, and CodeQL have succeeded.

#### Scenario: Security red blocks packaging
- GIVEN Security Testing failed
- WHEN Packaging is evaluated
- THEN Packaging does not start

### Requirement: Vite production build
Packaging SHALL run `npm run build` and SHALL fail if `dist/` is missing, `dist/index.html` is missing, or no JavaScript bundle exists. It SHALL fail if `dist/` looks like source (`package.json` or `node_modules` inside `dist/`).

#### Scenario: SPA output
- GIVEN `npm run build` succeeds
- WHEN Packaging verifies output
- THEN `dist/index.html` exists
- AND at least one `.js` or `.mjs` file exists under `dist/`

### Requirement: Zip plus nginx image
Packaging SHALL zip the `dist/` contents and SHALL always generate and build an `nginx:1.27-alpine` image serving that static tree (SPA try_files on port 80). It SHALL NOT use an application `Dockerfile` as the GHCR/CD image. It SHALL save a gzipped image tar.

#### Scenario: App Dockerfile is not the deploy image
- GIVEN the React repo contains a `Dockerfile`
- WHEN Packaging prepares the image
- THEN that file is moved aside
- AND the generated nginx + Vite `dist/` Dockerfile is used for `docker build`

#### Scenario: Image tar is non-empty
- GIVEN `docker build` succeeds
- WHEN Packaging saves the image
- THEN a gzipped tar artifact exists and is non-empty

### Requirement: GHCR push only off pull requests
Packaging SHALL push the image to `ghcr.io/<owner>/heavy_rental_web_portal` tagged with a new `x.y.z` semver and `:latest` when the event is not a pull request. The semver SHALL be the highest existing `x.y.z` tag on that GHCR package with the patch incremented; if no such tag exists, it SHALL be `1.0.0`. Packaging SHALL NOT overwrite an existing `x.y.z` tag. On a `develop` → `master` pull request it SHALL skip the push and still upload the tar.

#### Scenario: Published release pushes
- GIVEN a published GitHub Release triggered the release pipeline
- AND the highest GHCR `heavy_rental_web_portal` semver tag is `1.0.1` or none exist
- WHEN Packaging finishes the Docker build
- THEN `docker push` runs for `ghcr.io/<owner>/heavy_rental_web_portal:1.0.2` (or `1.0.0` when none exist) and `:latest`

#### Scenario: PR skips registry push
- GIVEN a pull request from `develop` to `master` triggered the release pipeline
- WHEN Packaging finishes the Docker build
- THEN no `docker push` runs
- AND the gzipped image tar is still uploaded

### Requirement: Vite build does not inline lab backends
`npm run build` SHALL NOT be given `VITE_*` REST/Haystack/API base URLs or Stripe `sk_` / AWS keys. Packaging SHALL fail if `dist/` contains `sk_live_` / `sk_test_`, AWS secret material, `jdbc:postgresql://`, or `localhost:8080` / `localhost:8000` / `127.0.0.1:8080` / `127.0.0.1:8000`. Stripe `pk_` SHALL NOT fail the scan.

#### Scenario: Lab URL in the bundle fails
- GIVEN `dist/assets/*.js` contains `http://localhost:8080`
- WHEN Packaging scans `dist/`
- THEN the job fails

### Requirement: Image nginx is replaceable SPA only
The generated `nginx-spa.conf` SHALL serve `try_files` for the SPA and SHALL NOT `proxy_pass` to a hostname. The Dockerfile SHALL NOT set `ENV`/`ARG` for `REST_BASE_URL`, `VITE_*`, `STRIPE_*`, `AWS_*`, or `PORTAL_IMAGE`, and SHALL NOT `COPY` a `.env`.

#### Scenario: Generated nginx has no API host
- GIVEN Packaging generated `nginx-spa.conf`
- WHEN the file is checked
- THEN it has no `proxy_pass http` or `proxy_pass https`

### Requirement: Image is cloud-ready and deployable after build
After `docker build`, Packaging SHALL inspect `Config.Env` (no baked REST/Vite/Stripe/AWS keys), SHALL confirm the image exposes `80/tcp`, SHALL confirm `/usr/share/nginx/html/index.html` and at least one JS bundle exist, and SHALL re-scan that tree for the same secret/lab-URL patterns. Packaging SHALL start the image, confirm `GET /` and a missing client route (`GET /spa-fallback-check`) on port 80 return HTML, and SHALL stop the container. Packaging SHALL NOT leave nginx running.

#### Scenario: index.html present and env clean
- GIVEN the image built
- WHEN Packaging proves the image
- THEN `index.html` exists in the html root
- AND at least one `.js` or `.mjs` file exists under the html root
- AND `Config.Env` does not contain `REST_BASE_URL`
- AND `80/tcp` is exposed

#### Scenario: Nginx serves the SPA
- GIVEN the image built
- WHEN Packaging starts the container
- THEN `GET /` on port 80 returns HTML
- AND `GET /spa-fallback-check` returns HTML
- AND the container is removed before Packaging finishes
