# Delta for portal-cd-academy-auth

## ADDED Requirements

### Requirement: Academy Vocareum credentials
Every AWS job SHALL use Environment `academy`. Credentials SHALL come from `$GITHUB_EVENT_PATH` form fields or Environment secrets `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_SESSION_TOKEN`. Jobs SHALL `::add-mask::` those values before `$GITHUB_ENV`. The configuration SHALL NOT interpolate `${{ inputs.aws_access_key_id }}` (or secret/token) in `env:`.

#### Scenario: Wrong Environment
- GIVEN `aws_environment` is not `academy`
- WHEN the workflow runs
- THEN a job fails and no AWS calls succeed

#### Scenario: Missing keys
- GIVEN the form fields and Environment secrets are all empty
- WHEN `assert-lab` runs
- THEN the job fails asking to Start Lab and paste AWS Details

### Requirement: Academy variables are runner and image tag only
Environment `academy` SHALL expose Vocareum AWS secrets (or Run form keys), `AWS_REGION`, `PORTAL_IMAGE`, `IMAGE_HTTP_URL`, and variable `VITE_STRIPE_PUBLISHABLE_KEY` (`pk_` only). It SHALL NOT be the source of `REST_BASE_URL`, `VITE_*`, `VITE_API_TARGET`, Stripe `sk_` / `whsec_`, `HAYSTACK_BASE_URL`, `APP_CORS_*`, JWT, or RDS. `configure-only` MAY use stock `nginx` when `PORTAL_IMAGE` is empty. `deploy` SHALL NOT.

#### Scenario: GitHub REST_BASE_URL does not fill guest .env
- GIVEN someone set a GitHub variable `REST_BASE_URL`
- AND `heavy-rental/portal` has a different `REST_BASE_URL`
- WHEN configure-only writes `.env`
- THEN guest `.env` has the SM value
- AND the GitHub variable is unused

#### Scenario: configure-only allows stock nginx
- GIVEN `PORTAL_IMAGE` is empty
- AND `action=configure-only`
- WHEN ansible-portal runs
- THEN `portal_image` is `nginx`
