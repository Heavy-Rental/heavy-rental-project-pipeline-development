# Delta for portal-ci-release

## Purpose

Release packaging produces a Vite `dist/` zip and an nginx Docker image tar after Integration and Quality Control pass. DAST scans that image. Publish then pushes public GHCR and creates the GitHub Release. Security Testing, CodeQL, and REST Endpoint Tests stay on Integration CI.

## ADDED Requirements

### Requirement: Packaging waits for gates
Packaging SHALL run only after Integration and Quality Control have succeeded. It SHALL NOT wait for Security Testing or CodeQL (those jobs are Integration CI only).

#### Scenario: Quality Control red blocks packaging
- GIVEN Quality Control failed
- WHEN Packaging is evaluated
- THEN Packaging does not start

### Requirement: Vite api-mode build
Packaging SHALL run `npx tsc -b` then `npx vite build --mode api` and SHALL fail if `dist/` is missing, `dist/index.html` is missing, or no JavaScript bundle exists. It SHALL fail if `dist/` looks like source (`package.json` or `node_modules` inside `dist/`). It SHALL NOT run `npm run build` (`MODE=production`).

#### Scenario: SPA output
- GIVEN `npx vite build --mode api` succeeds
- WHEN Packaging verifies output
- THEN `dist/index.html` exists
- AND at least one `.js` or `.mjs` file exists under `dist/`

### Requirement: Zip plus nginx image tar
Packaging SHALL zip the `dist/` contents and SHALL always generate and build an `nginx:1.27-alpine` image serving that static tree (SPA try_files on port 80). It SHALL NOT use an application `Dockerfile` as the GHCR/CD image. It SHALL save a gzipped image tar. Packaging SHALL NOT `docker push`.

#### Scenario: App Dockerfile is not the deploy image
- GIVEN the React repo contains a `Dockerfile`
- WHEN Packaging prepares the image
- THEN that file is moved aside
- AND the generated nginx + Vite `dist/` Dockerfile is used for `docker build`

#### Scenario: Image tar is non-empty
- GIVEN `docker build` succeeds
- WHEN Packaging saves the image
- THEN a gzipped tar artifact `heavy_rental_web_portal-image.tar.gz` exists and is non-empty

#### Scenario: Packaging does not push
- GIVEN Packaging finished the Docker build
- WHEN Packaging completes
- THEN no `docker push` runs in Packaging
- AND the gzipped image tar is still uploaded for DAST and Publish

### Requirement: Vite production profile is scanned before vite build
Packaging SHALL seed `.env.production` from the app checkout (`.env.production` or `docs/samples/.env.production`) or generated empty-backend defaults. That file is a **scan input**; `vite build --mode api` SHALL load `.env.api` (process env still empties `VITE_API_TARGET` / `VITE_*` backends). It SHALL fail if that file assigns `sk_`, `whsec_`, `REST_BASE_URL` / `HAYSTACK_BASE_URL` / non-empty `VITE_*` backend URLs (except a same-origin path), `APP_JWT_SECRET`, `POSTGRES_*`, or lab `localhost:8080` / `8000`. Packaging SHALL run `npx tsc -b` then `npx vite build --mode api` so `import.meta.env.MODE` is `api` (Spring login, rental-plan cart, deposit). It SHALL pass empty process-env `VITE_API_TARGET`, `VITE_API_URL`, `VITE_REST_*`, and `VITE_HAYSTACK_*` (overrides app `.env.api` compose hostname). Packaging SHALL NOT `COPY` `.env` / `.env.production` into the nginx image.

#### Scenario: Lab URL in .env.production fails
- GIVEN app `.env.production` contains `VITE_REST_BASE_URL=http://localhost:8080`
- WHEN Packaging scans the file
- THEN the job fails before `vite build`

#### Scenario: Academy image is Vite mode api
- GIVEN Packaging builds the SPA
- WHEN `vite build` runs
- THEN the command includes `--mode api`
- AND process env `VITE_API_TARGET` is empty

### Requirement: Academy Stripe publishable key is baked at Packaging
Packaging SHALL use Environment `academy` and SHALL pass non-empty `vars.VITE_STRIPE_PUBLISHABLE_KEY` into `vite build --mode api` as process env. Empty SHALL warn and SHALL NOT fail. A value starting with `sk_` or `whsec_` SHALL fail. Packaging SHALL NOT pass `STRIPE_API_KEY`. Fast Feedback and Integration CI SHALL NOT set `environment:`.

#### Scenario: Academy pk_ is injected
- GIVEN Environment `academy` variable `VITE_STRIPE_PUBLISHABLE_KEY` is `pk_test_example`
- WHEN Packaging runs `vite build --mode api`
- THEN process env `VITE_STRIPE_PUBLISHABLE_KEY` is that value
- AND `STRIPE_API_KEY` is empty

### Requirement: Vite build does not inline lab backends
The Vite build SHALL NOT be given `VITE_*` REST/Haystack/API base URLs, `VITE_API_TARGET` hostnames, or Stripe `sk_` / AWS keys. Packaging SHALL fail if `dist/` contains `sk_live_` / `sk_test_`, AWS secret material, `jdbc:postgresql://`, `heavy-rental-rest-api`, `localhost:8080` / `localhost:8000` / `127.0.0.1:4010`, or `127.0.0.1:8080` / `127.0.0.1:8000`. Stripe `pk_` SHALL NOT fail the scan.

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

### Requirement: DAST scans the packaged image
DAST SHALL run after Packaging succeeds. It SHALL start the packaged image and run OWASP ZAP (fail if exit ≥ 2), Dastardly (fail if exit ≠ 0), and Nuclei (report-only; `continue-on-error`). It SHALL upload `dast-reports/` including `combined-dast-report.pdf` (artifact `dast-combined-report-pdf`).

#### Scenario: DAST needs Packaging
- GIVEN Packaging failed
- WHEN DAST is evaluated
- THEN DAST does not start

### Requirement: Publish pushes GHCR and creates the GitHub Release
Publish SHALL run after Packaging and DAST succeed. It SHALL push the image to `ghcr.io/<owner>/heavy_rental_web_portal` tagged with a new `x.y.z` semver and `:latest`. The semver SHALL be the highest existing `x.y.z` tag on that GHCR package with the patch incremented; if no such tag exists, it SHALL be `1.0.0`. Publish SHALL NOT overwrite an existing `x.y.z` tag. Publish SHALL create a GitHub Release on `master` (`gh release create`). The Release caller SHALL NOT subscribe to `release` or `pull_request` events.

#### Scenario: workflow_dispatch publishes
- GIVEN a `workflow_dispatch` triggered the release pipeline
- AND DAST succeeded
- AND the highest GHCR `heavy_rental_web_portal` semver tag is `1.0.1` or none exist
- WHEN Publish runs
- THEN `docker push` runs for `ghcr.io/<owner>/heavy_rental_web_portal:1.0.2` (or `1.0.0` when none exist) and `:latest`
- AND `gh release create` runs targeting `master`
