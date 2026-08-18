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
- Overlay only non-empty Haystack Environment Profile knobs onto the **guest** `.env` (ADR 0009). Do not docker build. Do not rewrite `/app/.env` inside the pulled image.
- Overlay keys include `APP_NAME`, `APP_ENV`, `LOG_LEVEL`, `INDEXING_ST_MODEL`, `PROJECT_AGENT_*`, `RECOMMEND_FANOUT_CAP` (same list as `haystack-cd-academy.yml`).
- Do not invent `LLM_API_KEY` when the Environment secret is empty

## Output

OpenSpec + ADR 0003 + ADR 0004 + ADR 0009 + `deploy-pipeline/ansible/` + compose jobs + `docs/BOOTSTRAP.md` + `docs/PREPARE-HAYSTACK-REPO.md` + `docs/samples/.env.prod`.
