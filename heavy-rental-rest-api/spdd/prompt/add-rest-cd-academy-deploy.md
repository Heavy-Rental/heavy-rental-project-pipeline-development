# REASONS Canvas: REST CD deploy

## Role

Implement Academy REST CD compose (branch 2) in `deploy-pipeline/`.

## Safeguards

- No terraform, no `stop` / `destroy`
- No `mvn package` / `docker build`
- No Ansible groups portal / haystack / neo4j
- No PAT on the guest; private GHCR fails closed
- No stock Tomcat when image fields are empty
- No `${{ inputs.aws_* }}` in `env:`
- Do not fail verify solely because Haystack is down

## Output

OpenSpec + ADR 0003 + `deploy-pipeline/ansible/` + compose jobs in `rest-api-cd-academy.yml`.
