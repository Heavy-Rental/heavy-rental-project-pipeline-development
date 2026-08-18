# REASONS Canvas: Haystack CD deploy

## Role

Implement Academy Haystack CD compose (branch 2).

## Safeguards

- No terraform, no portal/rest/neo4j groups
- No neo4j container
- No uv/docker build
- No PAT on the guest
- No stock image when fields empty
- Do not overlay `NEO4J_URI` or `NEO4J_POPULATE_URL` from GitHub vars (infra AWS)
- Overlay only non-empty Haystack Environment Profile knobs (ADR 0009)
- Do not invent `LLM_API_KEY` when the Environment secret is empty

## Output

OpenSpec + ADR 0003 + ADR 0004 + ADR 0009 + `deploy-pipeline/ansible/` + compose jobs + `docs/PREPARE-HAYSTACK-REPO.md`.
