# Delta for haystack-cd-profile-overlay

## Purpose

Haystack Environment `academy` or `AWS_ACTUAL` holds product Profile knobs. Infra `heavy-rental/haystack` holds AWS estate keys. CD overlays the former onto **guest** `.env` after SM map (ADR 0009). Setting those GitHub variables SHALL NOT change the GHCR image or `/app/.env` inside the pulled tag.

## ADDED Requirements

### Requirement: Overlay Haystack project Profile knobs
On `deploy` and `configure-only`, after SM → `.env` and Postgres aliases, the haystack role SHALL write non-empty Haystack Environment (`academy` or `AWS_ACTUAL`) variables/secrets for `APP_NAME`, `APP_ENV`, `LOG_LEVEL`, `NEED_DECOMPOSER`, `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, `LLM_TIMEOUT_SECONDS`, `LLM_TEMPERATURE`, `INDEXING_EMBEDDER`, `INDEXING_EMBEDDING_DIM`, `INDEXING_SPLIT_LENGTH`, `INDEXING_SPLIT_OVERLAP`, `INDEXING_OPENAI_EMBEDDING_MODEL`, `INDEXING_ST_MODEL`, `INDEXING_DOCUMENT_STORE`, `INDEXING_CHUNK_TTL_SECONDS`, `IDEMPOTENCY_TTL_SECONDS`, `INDEXING_VIA_AGENT_GATE`, `FLEET_BACKEND`, `PRICING_SCHEMA`, `NEO4J_BACKEND`, `NEO4J_POPULATE_TIMEOUT_SECONDS`, `RECOMMEND_VIA_AGENT_GRAPH`, `RECOMMEND_FANOUT_CAP`, `KG_ARTIFACT_DIR`, `KG_APPLY_TRANSFORMS`, `PROJECT_AGENT_MODE`, and `PROJECT_AGENT_TOP_K`. Empty Environment values SHALL leave the SM, image `/app/.env` (from `.env.prod`), or app default. The overlay SHALL write the **guest** `.env` only and SHALL NOT rebuild or mutate the image. The overlay SHALL NOT write `NEO4J_URI`, `NEO4J_POPULATE_URL`, `NEO4J_USER`, `NEO4J_PASSWORD`, `POSTGRES_*`, `DATABASE_URL`, `SOURCE_*`, or `TARGET_*`.

#### Scenario: NEED_DECOMPOSER set on academy
- GIVEN Environment `academy` variable `NEED_DECOMPOSER` is `llm`
- AND `LLM_API_KEY` is set as an Environment secret
- WHEN Haystack CD `configure-only` runs
- THEN guest `.env` contains `NEED_DECOMPOSER=llm` and `LLM_API_KEY`
- AND `NEO4J_URI` is still the SM Bolt NLB value
- AND `NEO4J_POPULATE_URL` is still `http://neo4j-populate:8089/v1/populate` from SM

#### Scenario: Empty Profile vars
- GIVEN those Environment variables are unset
- WHEN Haystack CD writes `.env`
- THEN `FLEET_BACKEND` stays `sql` from SM
- AND `NEED_DECOMPOSER` is not invented

#### Scenario: Academy overlay does not change the image
- GIVEN Environment `academy` variable `NEED_DECOMPOSER` is `llm`
- AND guests already run `ghcr.io/heavy-rental/haystack_recommender:1.0.0`
- WHEN Haystack CD `configure-only` runs
- THEN guest `.env` contains `NEED_DECOMPOSER=llm`
- AND compose still uses the same image tag
- AND `/app/.env` inside that image is unchanged

### Requirement: Estate URLs stay AWS-owned
`NEO4J_URI` SHALL come from Terraform Bolt NLB via infra `sync-secrets`. `NEO4J_POPULATE_URL` SHALL come from infra `sync-secrets` as `http://neo4j-populate:8089/v1/populate` (compose worker on `asg-haystack`). Haystack CD SHALL NOT accept GitHub variables for those two names.

#### Scenario: Project var cannot replace Bolt NLB
- GIVEN someone set a GitHub variable `NEO4J_URI`
- WHEN Haystack CD overlays Profile knobs
- THEN guest `.env` `NEO4J_URI` is unchanged from SM
