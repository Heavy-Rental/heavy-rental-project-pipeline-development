# REASONS Canvas: portal CD skeleton

**Historical (branch 1).** Compose, verify, and paid/OIDC are later changes. Do not treat fail-closed compose as current YAML.

## Role

Implement Academy portal CD discover only on `HR-165`.

## Safeguards

- No terraform, docker, ansible-playbook
- No `${{ inputs.aws_secret` interpolation
- No instance IDs on the form
- No SecretString or REST ALB URL in logs
- Environment must be `academy`

## Output

OpenSpec + ADR + `web-portal-cd-academy.yml`.
