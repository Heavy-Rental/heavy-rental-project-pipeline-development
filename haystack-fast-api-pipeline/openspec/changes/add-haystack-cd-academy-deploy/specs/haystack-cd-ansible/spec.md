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
After writing `.env` from `heavy-rental/haystack`, the haystack role SHALL add aliases when the app name is empty: `POSTGRES_HOSTNAME` from `POSTGRES_HOST`, `POSTGRES_DB` from `POSTGRES_DATABASE`, `POSTGRES_USER` from `POSTGRES_USERNAME`. When `FLEET_BACKEND` or `NEO4J_BACKEND` is absent it SHALL set `sql` and `bolt`. It SHALL NOT overwrite a key already present in the secret. It SHALL NOT invent `LLM_API_KEY`.

#### Scenario: SM uses POSTGRES_HOST only
- GIVEN `heavy-rental/haystack` has `POSTGRES_HOST` and no `POSTGRES_HOSTNAME`
- THEN `.env` contains both, same host
- AND `FLEET_BACKEND=sql` and `NEO4J_BACKEND=bolt` unless the secret already set them

### Requirement: Sidecar commands match the Release image
`postgres-haystack-sync` and `neo4j-populate` SHALL use `uv run python -m …` (same image as uvicorn). Verify SHALL still pass if those processes exit, as long as uvicorn answers on `:8000`. The playbook SHALL fail if uvicorn never answers.

#### Scenario: Modules missing from the current app image
- GIVEN the image has no `postgres_haystack_sync` / `neo4j_populate` packages
- THEN those services may crash-loop
- AND `verify` is still green if `GET :8000/docs` or `/health` is 200–302
