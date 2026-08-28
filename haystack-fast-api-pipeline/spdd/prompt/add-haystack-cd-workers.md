# REASONS Canvas: Haystack CD workers

## Role

Match Haystack CD compose workers to estate ADR 0020.

## Safeguards

- No uvicorn `python -m postgres_haystack_sync` / `neo4j_populate`
- No guest `docker build`
- No published host/ALB `:8089`
- Do not invent `SOURCE_HOST` / `SOURCE_PORT` / `SOURCE_DATABASE` or `TARGET_HOST` / `TARGET_PORT` / `TARGET_DATABASE`
- Do not overlay `NEO4J_URI` / `NEO4J_POPULATE_URL` / `POSTGRES_*` / `SOURCE_*` / `TARGET_*` from GitHub vars
- Do not fail `verify` on worker crash; uvicorn `:8000/health` **2xx** is the gate
- Copy estate `files/` + `compose.yml.j2`; do not invent a second worker contract

## Output

ADR 0011 + OpenSpec `haystack-cd-ansible` + `deploy-pipeline/ansible/roles/haystack/files/` + living `haystack-cd.md` / BOOTSTRAP / PREPARE.
