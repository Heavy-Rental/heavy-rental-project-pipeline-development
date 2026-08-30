# Spec: portal-cd-paid

## ADDED Requirements

### Requirement: Paid caller is OIDC-only
`portal-cd-paid-caller.yml` SHALL NOT declare Vocareum key inputs. `aws_environment` SHALL be `AWS_ACTUAL`. Missing `AWS_ROLE_TO_ASSUME` or a set `AWS_ACCESS_KEY_ID` SHALL fail before compose. The paid caller SHALL NOT pass `secrets: inherit` (Semgrep `yaml.github-actions.security.secrets-inherit`). Auth SHALL be `vars.AWS_ROLE_TO_ASSUME` plus `id-token: write`.

#### Scenario: Paid refuses academy
- GIVEN Environment `academy` on the paid caller
- THEN assert fails and Ansible does not run

#### Scenario: Paid does not inherit secrets
- GIVEN the paid caller `uses:` the shared reusable
- WHEN the job is declared
- THEN `secrets: inherit` is absent
- AND `id-token: write` is present

### Requirement: Paid Ansible SSM bucket
Paid portal CD SHALL pass `ansible_aws_ssm_bucket_name=heavy-rental-ssm-<account>-actual`. It SHALL NOT use the Terraform state bucket.

#### Scenario: Paid compose uses SSM bucket
- GIVEN Environment `AWS_ACTUAL` and a live OIDC session
- WHEN `action=deploy` runs Ansible
- THEN extra-var `ansible_aws_ssm_bucket_name` is the SSM bucket

### Requirement: Paid overlays the same Stripe pk_ extra-var
On `deploy` and `configure-only`, Environment `AWS_ACTUAL` variable `VITE_STRIPE_PUBLISHABLE_KEY` SHALL overlay guest `.env` the same way as academy (`pk_` only; `sk_` / `whsec_` fail). The overlay SHALL NOT rewrite `/usr/share/nginx/html`.

#### Scenario: Paid pk_ overlay does not rebuild the SPA
- GIVEN Environment `AWS_ACTUAL` variable `VITE_STRIPE_PUBLISHABLE_KEY` is a `pk_` value
- WHEN `action=configure-only` runs
- THEN guest `.env` contains that `pk_`
- AND the pulled image `dist/` is unchanged

### Requirement: Academy caller stays Vocareum-only
`portal-cd-academy-caller.yml` SHALL fail if `aws_environment` is not `academy`.

#### Scenario: AWS_ACTUAL on academy caller
- GIVEN Environment `AWS_ACTUAL` on the academy caller
- THEN assert fails
