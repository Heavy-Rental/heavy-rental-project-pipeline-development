# REASONS Canvas: Haystack CD skeleton

**Historical (branch 1).** These safeguards bound discover-only YAML. Live compose is [`../analysis/add-haystack-cd-academy-deploy.md`](../analysis/add-haystack-cd-academy-deploy.md). Do not treat “no ansible-playbook” as current CD behavior.

## Role

Implement Academy Haystack CD discover only.

## Safeguards

- No terraform, docker, ansible-playbook
- No `${{ inputs.aws_secret` interpolation
- No instance IDs on the form
- No SecretString or internal ALB URL in logs
- Environment must be `academy`
- Do not start Neo4j

## Output

OpenSpec + ADR + `haystack-cd-academy.yml`.
