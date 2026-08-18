# Delta for rest-cd-ansible

## ADDED Requirements

### Requirement: Re-run infra REST compose via SSM
On `action=deploy` or `action=configure-only`, after discover succeeds, the workflow SHALL run Ansible over `amazon.aws.aws_ssm` against `asg-rest` only. The playbook SHALL apply `guest_base` then `rest`. It SHALL use `--limit rest`. Compose limits SHALL stay `1g` / `1.0` on `:8080`. It SHALL fail if `rest_image` is empty.

#### Scenario: Deploy applies the resolved image
- GIVEN `action=deploy` and resolve-image succeeded
- WHEN ansible-rest runs
- THEN extra-vars include that `rest_image` and optional `image_http_url`

#### Scenario: configure-only refreshes secret
- GIVEN `action=configure-only`
- WHEN ansible-rest runs
- THEN it uses Environment `REST_IMAGE` or Run `image_ref`
- AND it fails if both are empty
- AND it rewrites `.env` from `heavy-rental/rest`
- AND non-empty Environment pricing vars (`DYNAMIC_PRICING_ENABLED`, `PRICING_DEFAULT_DISTANCE_KM`, `PRICING_ORIGIN_POSTAL_CODE`, `PRICING_DISTANCE_LOOKUP_ENABLED`) overlay onto `.env`
- AND empty pricing vars leave SM / Spring defaults
- AND the overlay does not replace RDS, Stripe, JWT, CORS, or OneMap keys

#### Scenario: No other groups
- GIVEN ansible-rest runs
- THEN inventory has no playable `portal`, `haystack`, or `neo4j` hosts
- AND the playbook does not include those roles
- AND it does not start Bolt or a public listener
