# Delta for portal-cd-ansible

## ADDED Requirements

### Requirement: Re-run infra portal compose via SSM
On `action=deploy` or `action=configure-only`, after discover succeeds, the workflow SHALL run Ansible over `amazon.aws.aws_ssm` against `asg-portal` only. The playbook SHALL apply `guest_base` then `portal`. It SHALL use `--limit portal`. It SHALL write nginx `location /api/` from `REST_BASE_URL` in `heavy-rental/portal`. It SHALL refuse `STRIPE_API_KEY`, `STRIPE_WEBHOOK_SECRET`, and PEM material on the portal `.env`. Compose limits SHALL stay `256m` / `0.5`.

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

#### Scenario: No other groups
- GIVEN ansible-portal runs
- THEN inventory has no playable `rest`, `haystack`, or `neo4j` hosts
- AND the playbook does not include those roles
