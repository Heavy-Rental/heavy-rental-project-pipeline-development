# Delta for haystack-cd-ansible

## ADDED Requirements

### Requirement: Re-run infra Haystack compose via SSM
On `deploy` or `configure-only`, Ansible SHALL use `amazon.aws.aws_ssm` against `asg-haystack` only (`guest_base` then `haystack`, `--limit haystack`). Limits SHALL stay §6.4a. The compose file SHALL NOT contain a `neo4j` service. `haystack_image` SHALL NOT be empty.

#### Scenario: configure-only
- GIVEN `HAYSTACK_IMAGE` or `image_ref` is set
- THEN `.env` is rewritten from `heavy-rental/haystack` and compose uses that tag
- AND both empty fails

#### Scenario: No other groups
- THEN inventory has no portal / rest / neo4j hosts
- AND Bolt is `NEO4J_URI` from SM (NLB), not localhost

### Requirement: Map Secrets Manager keys to names the FastAPI app reads
After writing `.env` from `heavy-rental/haystack`, the haystack role SHALL add aliases when the app name is empty: `POSTGRES_HOSTNAME` from `POSTGRES_HOST`, `POSTGRES_DB` from `POSTGRES_DATABASE`, `POSTGRES_USER` from `POSTGRES_USERNAME`. When `FLEET_BACKEND` or `NEO4J_BACKEND` is absent it SHALL set `sql` and `bolt`. It SHALL NOT overwrite a key already present in the secret unless the Haystack GitHub Environment overlay supplies that key. It SHALL NOT invent `LLM_API_KEY` when the Environment secret is empty.

### Requirement: Overlay Haystack project Profile knobs
On `deploy` and `configure-only`, after SM → `.env` and aliases, the haystack role SHALL write non-empty Haystack Environment `academy` variables/secrets for `APP_NAME`, `APP_ENV`, `LOG_LEVEL`, `NEED_DECOMPOSER`, `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_TIMEOUT_SECONDS`, `LLM_TEMPERATURE`, `INDEXING_EMBEDDER`, `INDEXING_EMBEDDING_DIM`, `INDEXING_SPLIT_LENGTH`, `INDEXING_SPLIT_OVERLAP`, `INDEXING_OPENAI_EMBEDDING_MODEL`, `INDEXING_ST_MODEL`, `INDEXING_DOCUMENT_STORE`, `INDEXING_CHUNK_TTL_SECONDS`, `IDEMPOTENCY_TTL_SECONDS`, `INDEXING_VIA_AGENT_GATE`, `FLEET_BACKEND`, `PRICING_SCHEMA`, `NEO4J_BACKEND`, `NEO4J_POPULATE_TIMEOUT_SECONDS`, `RECOMMEND_VIA_AGENT_GRAPH`, `RECOMMEND_FANOUT_CAP`, `KG_ARTIFACT_DIR`, `KG_APPLY_TRANSFORMS`, `PROJECT_AGENT_MODE`, and `PROJECT_AGENT_TOP_K`. Empty Environment values SHALL leave the SM, image `/app/.env` (from `.env.prod`), or app default. The overlay SHALL write the **guest** `.env` only. It SHALL NOT rebuild the image, SHALL NOT rewrite `/app/.env` inside the pulled tag, and SHALL NOT write `NEO4J_URI`, `NEO4J_POPULATE_URL`, `NEO4J_USER`, `NEO4J_PASSWORD`, `POSTGRES_*`, `DATABASE_URL`, `SOURCE_*`, or `TARGET_*`.

#### Scenario: NEED_DECOMPOSER set on academy
- GIVEN Environment `academy` variable `NEED_DECOMPOSER` is `llm`
- AND `LLM_API_KEY` is set as an Environment secret
- WHEN Haystack CD `configure-only` runs
- THEN guest `.env` contains `NEED_DECOMPOSER=llm` and `LLM_API_KEY`
- AND `NEO4J_URI` is still the SM Bolt NLB value

#### Scenario: Empty Profile vars
- GIVEN those Environment variables are unset
- WHEN Haystack CD writes `.env`
- THEN `FLEET_BACKEND` stays `sql` from SM
- AND `NEED_DECOMPOSER` is not invented

#### Scenario: SM uses POSTGRES_HOST only
- GIVEN `heavy-rental/haystack` has `POSTGRES_HOST` and no `POSTGRES_HOSTNAME`
- THEN `.env` contains both, same host
- AND `FLEET_BACKEND=sql` and `NEO4J_BACKEND=bolt` unless the secret already set them

### Requirement: Sync endpoints stay infra-owned
Haystack CD SHALL pass `SOURCE_HOST` / `SOURCE_PORT` / `SOURCE_DATABASE` and `TARGET_HOST` / `TARGET_PORT` / `TARGET_DATABASE` through from `heavy-rental/haystack` when present. It SHALL NOT invent those keys, SHALL NOT copy `heavy-rental/rest`, and SHALL NOT bake RDS hostnames into the image or the workflow YAML.

#### Scenario: SM already has SOURCE and TARGET
- GIVEN `heavy-rental/haystack` contains `SOURCE_HOST` (SoR RDS) and `TARGET_HOST` (Haystack RDS)
- WHEN `guest_base` writes `.env`
- THEN both keys are on `.env` unchanged
- AND Ansible does not add a different `SOURCE_HOST`

### Requirement: Sidecar commands match the Release image
`postgres-haystack-sync` and `neo4j-populate` SHALL use `uv run python -m …` (same image as uvicorn). Verify SHALL still pass if those processes exit, as long as uvicorn answers on `:8000`. The playbook SHALL fail if uvicorn never answers.

#### Scenario: Modules missing from the current app image
- GIVEN the image has no `postgres_haystack_sync` / `neo4j_populate` packages
- THEN those services may crash-loop
- AND `verify` is still green if `GET :8000/docs` or `/health` is 200–302
