# SPDD Analysis: add-portal-cd-academy-deploy

**Companion:** [REASONS Canvas](../prompt/add-portal-cd-academy-deploy.md)

## Problem

Branch 1 can see `asg-portal` but cannot load a CI nginx image or refresh `/api`. As-built first-compose is infra `deploy-projects` or this CD (not infra `apply`).

## Strategy

Copy estate `guest_base` + `portal`. Pipeline `resolve-image` chooses tag or tar. Ansible over SSM, `--limit portal`. Guest nginx `/api` is `REST_BASE_URL` with no trailing URI, `Host $proxy_host`, omit `Origin` (infra ADR 0018). Verify is SSM `GET /` (200–302), not `/api`.

## Success

`action=deploy` with a public GHCR or ECR tag (or tar **and** a matching compose tag) updates both portal guests. `verify` is green if nginx answers. `configure-only` rewrites `/opt/heavy-rental/.env` from `heavy-rental/portal` (`REST_BASE_URL` required; refuse `sk_` / webhook / PEM) and remounts `/api` (omit `Origin`; hairpin does not use Spring CORS). GitHub `academy` (or `AWS_ACTUAL`) is runner auth + `PORTAL_IMAGE` / `IMAGE_HTTP_URL` + optional `VITE_STRIPE_PUBLISHABLE_KEY` (`pk_` overlay writes guest `.env`; the SPA still uses the Release-baked key). Stock nginx allowed on configure-only only. Checkout `.env.api` / `.env.production` is ignored. No `npm`. Operator: `docs/BOOTSTRAP.md`, ADR 0008.
