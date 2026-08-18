# ADR 0007: Portal Release image is a static SPA; CD owns `/api`

- **Status:** Accepted
- **Date:** 2026-08-18
- **Change:** `add-portal-ci-pipeline` (image contract)
- **Related:** [0006](0006-portal-ci-stops-at-packaging.md), [0003](0003-reuse-infra-portal-ansible.md)

## Context

Vite inlines `import.meta.env.VITE_*` at `npm run build`. Academy compose does not give the SPA a Spring-style `.env`. Guest Ansible writes nginx `location /api/` → `REST_BASE_URL` from `heavy-rental/portal` and **mounts** that file over the image `default.conf`.

Baking `http://localhost:8080` or a lab ALB into the JS, or baking `REST_BASE_URL` into the image nginx, would pin every tag to one estate.

## Decision

Release always generates the `nginx:1.27-alpine` + Vite `dist/` Dockerfile (an app `Dockerfile` is not the GHCR/CD image). It builds with no `VITE_*` backend URLs. Packaging fails if `dist/` or the image html tree contains `sk_`, AWS secret material, JDBC URLs, or localhost:8080/8000. Generated nginx is try_files only. After `docker build`, inspect `Config.Env`, confirm `index.html` and a JS bundle exist, start the image, and require `GET /` plus a missing client route to return HTML. Stripe `pk_` is allowed; `sk_` is not.

## Consequences

- The same image works on any Academy lab once CD mounts `/api`.
- The SPA must call same-origin `/api` (or another path the guest nginx proxies). Hardcoded REST hosts fail Release.
- Runtime `config.js` injection is not this change.
