# REASONS Canvas: portal CD deploy

## Role

Implement Academy portal CD compose (branch 2) in `deploy-pipeline/`.

## Safeguards

- No terraform, no `stop` / `destroy`
- No `npm run build` / `docker build` (SPA was already built with npm in Release)
- No Ansible groups rest / haystack / neo4j
- No PAT on the guest; private GHCR fails closed
- No `STRIPE_API_KEY` / webhook / PEM on portal `.env`
- Guest `.env` from `heavy-rental/portal` only — do not read `.env.api` / `.env.production` or GitHub `REST_BASE_URL` / `VITE_*`
- Do not overlay GitHub `VITE_*` onto the image except `VITE_STRIPE_PUBLISHABLE_KEY` (`pk_`) onto guest `.env` (SPA still uses the Release-baked key)
- configure-only may use stock `nginx`; deploy must not
- No `${{ inputs.aws_* }}` in `env:`
- Do not fail verify solely because `/api` is down

## Output

OpenSpec + ADR 0003 + ADR 0008 + `deploy-pipeline/ansible/` + compose jobs in `web-portal-cd-academy.yml` + `docs/BOOTSTRAP.md` + `docs/samples/.env.production`.
