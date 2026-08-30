# Delta for portal-cd-ansible

## ADDED Requirements

### Requirement: Re-run infra portal compose via SSM
On `action=deploy` or `action=configure-only`, after discover succeeds, the workflow SHALL run Ansible over `amazon.aws.aws_ssm` against `asg-portal` only. The playbook SHALL apply `guest_base` then `portal`. It SHALL use `--limit portal`. It SHALL write nginx `location /api/` from `REST_BASE_URL` in `heavy-rental/portal` (Terraform REST ALB via infra `sync-secrets`). It SHALL refuse `STRIPE_API_KEY`, `STRIPE_WEBHOOK_SECRET`, and PEM material on the portal `.env`. It SHALL NOT overlay GitHub `VITE_*` into the image or rewrite `/usr/share/nginx/html`. Environment `VITE_STRIPE_PUBLISHABLE_KEY` (`pk_` only) MAY be written onto guest `.env` after SM (see below) and SHALL NOT change the image `dist/`. Compose limits SHALL stay `256m` / `0.5`.

#### Scenario: Deploy applies the resolved image
- GIVEN `action=deploy` and resolve-image succeeded
- WHEN ansible-portal runs
- THEN extra-vars include that `portal_image` and optional `image_http_url`
- AND the play does not invent a different registry URL

#### Scenario: configure-only refreshes secret and proxy
- GIVEN `action=configure-only`
- WHEN ansible-portal runs
- THEN it uses Environment `PORTAL_IMAGE` or stock `nginx`
- AND it rewrites `.env` and `/api` from `heavy-rental/portal`

#### Scenario: REST_BASE_URL missing
- GIVEN `heavy-rental/portal` has no `REST_BASE_URL=https?://…`
- WHEN the portal role runs
- THEN the play fails

#### Scenario: Academy VITE vars do not change the image
- GIVEN someone set a GitHub variable `VITE_REST_BASE_URL`
- WHEN portal CD `configure-only` runs
- THEN nginx `/api` still comes from SM `REST_BASE_URL`
- AND the pulled image `dist/` is unchanged

#### Scenario: No other groups
- GIVEN ansible-portal runs
- THEN inventory has no playable `rest`, `haystack`, or `neo4j` hosts
- AND the playbook does not include those roles

### Requirement: Guest .env is Secrets Manager only
On `deploy` and `configure-only`, `guest_base` SHALL write `/opt/heavy-rental/.env` by mapping JSON from `heavy-rental/portal` only. It SHALL NOT read the React checkout `.env.api`, `.env.mock`, or `.env.production`. It SHALL NOT copy GitHub Environment `REST_BASE_URL` or other `VITE_*` onto that file. The exception is Environment `VITE_STRIPE_PUBLISHABLE_KEY` (`pk_` only), overlaid after SM (see below). The portal role SHALL fail if guest `.env` lacks `REST_BASE_URL=https?://…`. It SHALL fail if guest `.env` contains `STRIPE_API_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_SECRET_KEY`, or PEM material.

#### Scenario: SM maps to guest .env
- GIVEN `heavy-rental/portal` is `{"REST_BASE_URL":"http://rest.example:8080","STRIPE_PUBLISHABLE_KEY":"pk_test_x"}`
- WHEN configure-only writes `.env`
- THEN `/opt/heavy-rental/.env` contains `REST_BASE_URL=http://rest.example:8080`
- AND nginx `/api` uses that URL

#### Scenario: App dotenv is ignored
- GIVEN the checkout has `.env.api` with `VITE_API_TARGET=http://heavy-rental-rest-api:8080`
- WHEN configure-only runs
- THEN guest `.env` is still only the SM map
- AND `VITE_API_TARGET` is not written

#### Scenario: Stripe secret on portal .env fails
- GIVEN `heavy-rental/portal` contains `STRIPE_API_KEY`
- WHEN `guest_base` writes `.env`
- THEN the portal play fails

### Requirement: Overlay Environment Stripe pk_ after SM
On `deploy` and `configure-only`, when Environment `academy` or `AWS_ACTUAL` variable `VITE_STRIPE_PUBLISHABLE_KEY` is a non-empty `pk_` value, the portal role SHALL write `VITE_STRIPE_PUBLISHABLE_KEY` and `STRIPE_PUBLISHABLE_KEY` onto guest `.env` after the SM map. Empty SHALL leave SM. `sk_` / `whsec_` SHALL fail. This overlay SHALL NOT change `/usr/share/nginx/html` (the SPA still uses the key baked at Release).

#### Scenario: Environment pk_ overlays SM
- GIVEN Environment `VITE_STRIPE_PUBLISHABLE_KEY` is `pk_test_academy`
- AND SM has a different `STRIPE_PUBLISHABLE_KEY`
- WHEN configure-only or deploy runs
- THEN guest `.env` contains `VITE_STRIPE_PUBLISHABLE_KEY=pk_test_academy`
- AND `/usr/share/nginx/html` is unchanged
