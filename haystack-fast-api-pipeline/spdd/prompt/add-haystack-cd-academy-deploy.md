# REASONS Canvas: Haystack CD deploy

## Role

Implement Academy Haystack CD compose (branch 2).

## Safeguards

- No terraform, no portal/rest/neo4j groups
- No neo4j container
- No uv/docker build
- No PAT on the guest
- No stock image when fields empty

## Output

OpenSpec + ADR 0003 + ADR 0004 + `deploy-pipeline/ansible/` + compose jobs + `docs/PREPARE-HAYSTACK-REPO.md`.
