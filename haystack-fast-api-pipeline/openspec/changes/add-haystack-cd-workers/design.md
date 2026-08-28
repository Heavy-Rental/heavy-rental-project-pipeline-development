# Design: CD copies estate Haystack workers

Keep ADR 0003 copy-not-fork. Sidecar **runtime** follows infra ADR 0020 / Haystack ADR 0011. Profile overlay and SM **host** rules stay ADR 0004 / 0009.

## Decisions

1. Same three services, limits, and no-`neo4j` check as estate.
2. Workers are public images + bind-mounted scripts under `/opt/heavy-rental/workers/`. `restart: unless-stopped`.
3. `neo4j-populate` pip-installs `psycopg[binary]==3.2.9` and `neo4j==5.28.1` then runs `populate-neo4j-from-haystack.sh`.
4. `:8089` is Compose DNS only.
5. Credential aliases fill missing worker names only. Overlay still must not write `SOURCE_*` / `TARGET_*` / `POSTGRES_*` / `NEO4J_URI` / `NEO4J_POPULATE_URL`.
