# REASONS Canvas: REST CD skeleton

## Role

Implement Academy REST CD discover only.

## Safeguards

- No terraform, docker, ansible-playbook
- No `${{ inputs.aws_secret` interpolation
- No instance IDs on the form
- No SecretString or internal ALB URL in logs
- Environment must be `academy`
- Do not use CI Environments `integration` / `production`

## Output

OpenSpec + ADR + `rest-api-cd-academy.yml`.
