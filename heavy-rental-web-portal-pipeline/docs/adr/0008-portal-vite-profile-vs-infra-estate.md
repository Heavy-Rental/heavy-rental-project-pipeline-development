# ADR 0008: Portal Vite profile is build-time; REST hosts come from AWS

- **Status:** Accepted
- **Date:** 2026-08-18
- **Amended:** 2026-08-18 — three stores for CD `configure-only`
- **Amended:** 2026-08-26 — build command is `vite build --mode api` (not `npm run build`)
- **Amended:** 2026-08-29 — `APP_CORS_ALLOWED_ORIGINS` includes portal **and** public REST ALB origins (infra ADR 0018); portal `/api` hairpins via NAT
- **Amended:** 2026-08-30 — `.env.production` is a Release scan input (`--mode api` loads `.env.api`); CD `pk_` overlay applies on `academy` or `AWS_ACTUAL` and does not reconfigure the SPA
- **Amended:** 2026-08-30 — portal nginx `/api` omits `Origin`; `APP_CORS_ALLOWED_ORIGINS` is for **direct** REST ALB browser calls (infra ADR 0018), not the same-origin hairpin
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
| Terraform ALBs via `sync-secrets` | `REST_BASE_URL=http://<rest_alb_dns>:8080` → portal SM (CD nginx `/api`; public DNS, NAT hairpin; **omit `Origin`**). `HAYSTACK_BASE_URL` and `APP_CORS_ALLOWED_ORIGINS=http://<portal_alb_dns>,http://<rest_alb_dns>:8080` → **REST SM only** (direct REST ALB callers; not the portal `/api` hop) |
| Infra Environment `academy` secrets | Stripe trio, JWT, optional OneMap. Portal SM gets `pk_` only. `sk_` / `whsec_` stay on REST |
| Release `vite build --mode api` | `MODE=api` (Spring login). Empty `VITE_API_TARGET` (same-origin `/api`). Optional Stripe `pk_` from `.env.api` / build env. `.env.production` is scanned; `--mode api` loads `.env.api` unless process env wins |
| Portal Environment `academy` or `AWS_ACTUAL` | Vocareum keys (academy only) or OIDC role (`AWS_ACTUAL`); `PORTAL_IMAGE` / `IMAGE_HTTP_URL`; **`VITE_STRIPE_PUBLISHABLE_KEY`** (`pk_` only). Release Packaging (`environment: academy`) bakes it into `vite build --mode api`. CD overlays the same name onto guest `.env` (does **not** rewrite `dist/`). Other `VITE_*` stay off these Environments |
| Never in the React bundle or nginx image | `REST_BASE_URL`, Haystack URL, RDS, JWT, Stripe `sk_` / `whsec_`, OneMap, CORS, AWS keys |

Portal CD overlays **nginx `/api`**, not the Vite bundle. `/api` is same-origin; nginx omits `Origin` so Spring CORS is not on that hop. Setting a GitHub `VITE_*` variable does not rebuild GHCR. CD overlay of `VITE_STRIPE_PUBLISHABLE_KEY` writes guest `.env` only; the browser still uses the key baked at Release.

### `configure-only` stores

| Store | Reads? | Keys |
| --- | --- | --- |
| GitHub Environment `academy` or `AWS_ACTUAL` | Runner / compose tag + Stripe `pk_` | Vocareum secrets or Run form (academy); OIDC role (`AWS_ACTUAL`); `AWS_REGION`; `PORTAL_IMAGE` (empty → stock `nginx`); `IMAGE_HTTP_URL`; `VITE_STRIPE_PUBLISHABLE_KEY` |
| Guest `/opt/heavy-rental/.env` | Yes — SM `heavy-rental/portal`, then optional `pk_` overlay | **Required** `REST_BASE_URL`. SM may also write `STRIPE_PUBLISHABLE_KEY` / `VITE_STRIPE_PUBLISHABLE_KEY` (SPA cannot read them). Academy / `AWS_ACTUAL` `pk_` overlays those names after SM. Refuse `sk_` / webhook / PEM |
| App `.env.api` / `.env.mock` / `.env.production` | **No** | Release only. `.env.production` is scanned; `--mode api` loads `.env.api`. `MODE=api` is a build flag, not a CD overlay |

`configure-only` SHALL NOT run `npm` or `vite`. It SHALL NOT copy GitHub `REST_BASE_URL` onto the guest file. It MAY overlay Environment `VITE_STRIPE_PUBLISHABLE_KEY` (`pk_` only) onto guest `.env` after SM; that overlay SHALL NOT rewrite `/usr/share/nginx/html`.

## Consequences

- Same GHCR tag works on any Academy lab once CD mounts `/api` from SM.
- Changing SPA product knobs or Stripe `pk_` in the bundle requires `vite build --mode api` + a new image tag + `action=deploy`.
- Changing the REST host is infra `configure-only` / `apply` (Terraform DNS → SM) then portal CD `configure-only`.
- Sample: [`../samples/.env.production`](../samples/.env.production). Operator: [`../BOOTSTRAP.md`](../BOOTSTRAP.md).
