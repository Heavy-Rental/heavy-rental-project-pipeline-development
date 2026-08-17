# REASONS Canvas: portal CD deploy

## Role

Implement Academy portal CD compose (branch 2) in `deploy-pipeline/`.

## Safeguards

- No terraform, no `stop` / `destroy`
- No `npm run build` / `docker build`
- No Ansible groups rest / haystack / neo4j
- No PAT on the guest; private GHCR fails closed
- No `STRIPE_API_KEY` / webhook / PEM on portal `.env`
- No `${{ inputs.aws_* }}` in `env:`
- Do not fail verify solely because `/api` is down

## Output

OpenSpec + ADR 0003 + `deploy-pipeline/ansible/` + compose jobs in `web-portal-cd-academy.yml`.
