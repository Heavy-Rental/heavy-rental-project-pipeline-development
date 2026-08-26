# Delta for rest-cd-academy-auth

**Amended** by [`../../../add-rest-cd-paid-deploy/specs/rest-cd-paid/spec.md`](../../../add-rest-cd-paid-deploy/specs/rest-cd-paid/spec.md): the shared reusable accepts `academy` or `AWS_ACTUAL`. This file remains the academy-caller contract.

## ADDED Requirements

### Requirement: Academy Vocareum credentials
Every AWS job on the **academy caller** SHALL use Environment `academy`. Credentials SHALL come from `$GITHUB_EVENT_PATH` form fields or Environment secrets `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_SESSION_TOKEN`. Jobs SHALL `::add-mask::` those values before `$GITHUB_ENV`. The configuration SHALL NOT interpolate `${{ inputs.aws_access_key_id }}` (or secret/token) in `env:`. CI Environments `integration` / `production` SHALL NOT be used as CD auth.

#### Scenario: Wrong Environment
- GIVEN `aws_environment` is not `academy`
- WHEN the workflow runs
- THEN a job fails and no AWS calls succeed

#### Scenario: Missing keys
- GIVEN the form fields and Environment secrets are all empty
- WHEN `assert-lab` runs
- THEN the job fails asking to Start Lab and paste AWS Details
