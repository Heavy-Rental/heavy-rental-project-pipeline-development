# ADR 0008: Portal Vite profile is build-time; REST hosts come from AWS

- **Status:** Accepted
- **Date:** 2026-08-18
- **Amended:** 2026-08-18 — three stores for CD `configure-only`
- **Amended:** 2026-08-26 — build command is `vite build --mode api` (not `npm run build`)
- **Change:** `add-portal-ci-pipeline` / `add-portal-cd-academy-deploy` (env ownership)
- **Related:** [0007](0007-portal-ci-release-image-cloud-ready.md), [0003](0003-reuse-infra-portal-ansible.md)
- **Infra ground truth:** `aws-infra-academy.yml` → `scripts/sync-secrets.sh`
- **Spring REST:** [heavy-rental-spring-rest-api](https://github.com/Heavy-Rental/heavy-rental-spring-rest-api) `application.properties` / pipeline sample `application-prod.properties`

## Context

Haystack ships a sanitized `.env` inside the uvicorn image because pydantic reads it at runtime. Spring REST loads `application-prod.properties` with `${ENV}` placeholders filled from `heavy-rental/rest`. The portal is a **React + npm + Vite** SPA: `import.meta.env.VITE_*` is inlined by `vite build --mode api`. nginx does not run Node. A haystack-style `COPY .env` or a Spring-style academy overlay of `VITE_*` would not configure the running browser app.

Spring REST already consumes the estate keys the portal must **not** bake: `POSTGRES_*`, `HAYSTACK_BASE_URL`, `APP_CORS_ALLOWED_ORIGINS`, `STRIPE_API_KEY` / webhook, `APP_JWT_SECRET`, OneMap, pricing flags. Infra `sync-secrets` writes those to `heavy-rental/rest` and writes `REST_BASE_URL` + Stripe `pk_` to `heavy-rental/portal`.

## Decision

| Owner | Keys |
| --- | --- |
| Terraform ALBs via `sync-secrets` | `REST_BASE_URL=http://<rest_alb_dns>:8080` → portal SM (CD nginx `/api`). `HAYSTACK_BASE_URL` and `APP_CORS_ALLOWED_ORIGINS=http://<portal_alb_dns>` → **REST SM only** |
| Infra Environment `academy` secrets | Stripe trio, JWT, optional OneMap. Portal SM gets `pk_` only. `sk_` / `whsec_` stay on REST |
| Release `vite build --mode api` | `MODE=api` (Spring login). Empty `VITE_API_TARGET` (same-origin `/api`). Optional Stripe `pk_` from `.env.api` / build env. `.env.production` is scanned; `--mode api` loads `.env.api` unless process env wins |
| Portal Environment `academy` | Vocareum keys; `PORTAL_IMAGE` / `IMAGE_HTTP_URL`; **`VITE_STRIPE_PUBLISHABLE_KEY`** (`pk_` only). Release Packaging (`environment: academy`) bakes it into `vite build --mode api`. CD overlays the same name onto guest `.env`. Other `VITE_*` stay off academy |
| Never in the React bundle or nginx image | `REST_BASE_URL`, Haystack URL, RDS, JWT, Stripe `sk_` / `whsec_`, OneMap, CORS, AWS keys |

Portal CD overlays **nginx `/api`**, not Vite. Setting a GitHub `VITE_*` variable does not rebuild GHCR and does not change the running SPA.

### `configure-only` stores

| Store | Reads? | Keys |
| --- | --- | --- |
| GitHub Environment `academy` | Runner / compose tag + Stripe `pk_` | Vocareum secrets or Run form; `AWS_REGION`; `PORTAL_IMAGE` (empty → stock `nginx`); `IMAGE_HTTP_URL`; `VITE_STRIPE_PUBLISHABLE_KEY` |
| Guest `/opt/heavy-rental/.env` | Yes — SM `heavy-rental/portal` only | **Required** `REST_BASE_URL`. SM may also write `STRIPE_PUBLISHABLE_KEY` / `VITE_STRIPE_PUBLISHABLE_KEY` (SPA cannot read them). Refuse `sk_` / webhook / PEM |
| App `.env.api` / `.env.mock` / `.env.production` | **No** | Release `npm` / Vite only. `MODE=api` is not applied here |

`configure-only` SHALL NOT run `npm` or `vite`. It SHALL NOT copy GitHub `REST_BASE_URL` onto the guest file.

## Consequences

- Same GHCR tag works on any Academy lab once CD mounts `/api` from SM.
- Changing SPA product knobs or Stripe `pk_` in the bundle requires `vite build --mode api` + a new image tag + `action=deploy`.
- Changing the REST host is infra `configure-only` / `apply` (Terraform DNS → SM) then portal CD `configure-only`.
- Sample: [`../samples/.env.production`](../samples/.env.production). Operator: [`../BOOTSTRAP.md`](../BOOTSTRAP.md).
