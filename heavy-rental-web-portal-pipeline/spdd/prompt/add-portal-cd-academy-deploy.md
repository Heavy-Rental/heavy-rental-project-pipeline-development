# REASONS Canvas: portal CD deploy

## Role

Implement Academy portal CD compose (branch 2) in `deploy-pipeline/`.

## Safeguards

- No terraform, no `stop` / `destroy`
- No `npm run build` / `vite build` / `docker build` (SPA was already built with `vite build --mode api` in Release)
- No Ansible groups rest / haystack / neo4j
- No PAT on the guest; private GHCR fails closed
- No `STRIPE_API_KEY` / webhook / PEM on portal `.env`
- Guest `.env` from `heavy-rental/portal` only — do not read `.env.api` / `.env.production` or GitHub `REST_BASE_URL` / other `VITE_*`
- Do not overlay GitHub `VITE_*` onto the image. Exception: Environment `VITE_STRIPE_PUBLISHABLE_KEY` (`pk_` only) onto guest `.env` after SM (SPA still uses the Release-baked key; do not rewrite `dist/`)
- configure-only may use stock `nginx`; deploy must not
- No `${{ inputs.aws_* }}` in `env:`
- Do not fail verify solely because `/api` is down
- Guest nginx `/api` MUST omit `Origin` (`proxy_set_header Origin ""`), keep `Host $proxy_host`, and MUST NOT add a trailing URI on `proxy_pass`. Do not depend on Spring `APP_CORS_ALLOWED_ORIGINS` for the hairpin

## Output

OpenSpec + ADR 0003 + ADR 0008 + `deploy-pipeline/ansible/` + compose jobs in `web-portal-cd-academy.yml` + `docs/BOOTSTRAP.md` + `docs/samples/.env.production`.
