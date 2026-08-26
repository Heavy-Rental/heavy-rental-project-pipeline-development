# ADR 0007: Portal Release image is a static SPA; CD owns `/api`

- **Status:** Accepted
- **Date:** 2026-08-18
- **Amended:** 2026-08-18 — Vite `.env.production` at `vite build --mode api`; still no image `COPY .env`
- **Amended:** 2026-08-26 — GHCR push is Publish after DAST; Packaging does not `docker push`
- **Change:** `add-portal-ci-pipeline` (image contract)
- **Related:** [0006](0006-portal-ci-stops-at-packaging.md), [0003](0003-reuse-infra-portal-ansible.md), [0008](0008-portal-vite-profile-vs-infra-estate.md)

## Context

Vite inlines `import.meta.env.VITE_*` at `vite build --mode api`. Academy compose does not give the SPA a Spring-style `.env`. Guest Ansible writes nginx `location /api/` → `REST_BASE_URL` from `heavy-rental/portal` and **mounts** that file over the image `default.conf`.

Baking `http://localhost:8080` or a lab ALB into the JS, or baking `REST_BASE_URL` into the image nginx, would pin every tag to one estate.

## Decision

Release always generates the `nginx:1.27-alpine` + Vite `dist/` Dockerfile (an app `Dockerfile` is not the GHCR/CD image). It is a **React + npm** build: Node 22, `npm ci`, `npx tsc -b`, `npx vite build --mode api` (not `npm run build`). Packaging seeds/scans `.env.production` with process-env empty `VITE_API_TARGET` and `VITE_*` backends (overrides `.env.api` compose hostname). It SHALL NOT `COPY` that file into nginx. Packaging fails if the file, `dist/`, or the image html tree contains `sk_`, `REST_BASE_URL=http`, Haystack hosts, AWS secret material, JDBC URLs, or localhost:8080/8000. Generated nginx is try_files only. After `docker build`, inspect `Config.Env`, confirm `index.html` and a JS bundle exist, start the image, and require `GET /` plus a missing client route to return HTML. Packaging uploads the image tar and does not `docker push`. Publish (after DAST) pushes GHCR `heavy_rental_web_portal:<semver>` + `:latest` and creates the GitHub Release. Stripe `pk_` is allowed; `sk_` is not.

## Consequences

- The same image works on any Academy lab once CD mounts `/api`.
- The SPA must call same-origin `/api` (or another path the guest nginx proxies). Hardcoded REST hosts fail Release.
- Runtime `config.js` injection is not this change.
- Sample: [`../samples/.env.production`](../samples/.env.production). Product profile is a **build** input, not an image layer (ADR 0008).
