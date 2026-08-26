# Spec: rest-cd-paid

## MODIFIED Requirements

### Requirement: Academy Vocareum credentials
`rest-cd-academy-auth` applied to every AWS job using Environment `academy`. That remains true for the **academy caller**. The shared reusable workflow `rest-api-cd-academy.yml` SHALL accept `academy` **or** `AWS_ACTUAL`. Paid jobs SHALL use Environment `AWS_ACTUAL` and SHALL NOT interpolate Vocareum key inputs.

#### Scenario: Reusable accepts both profiles
- GIVEN `aws_environment` is `academy` or `AWS_ACTUAL`
- WHEN `assert-lab` (`Assert AWS profile`) runs
- THEN the job continues to STS (caller already refused the wrong Environment)

#### Scenario: Reusable refuses unknown Environments
- GIVEN `aws_environment` is neither `academy` nor `AWS_ACTUAL`
- WHEN `assert-lab` runs
- THEN the job fails and no AWS calls succeed

## ADDED Requirements

### Requirement: Paid caller is OIDC-only
`rest-api-cd-paid-caller.yml` SHALL NOT declare Vocareum key inputs. Environment SHALL be `AWS_ACTUAL`.

#### Scenario: Paid refuses academy
- GIVEN Environment `academy` on the paid caller
- THEN assert fails

### Requirement: Paid Ansible SSM bucket
Paid REST CD SHALL use `heavy-rental-ssm-<account>-actual` for `ansible_aws_ssm_bucket_name`.

#### Scenario: Paid compose uses SSM bucket
- GIVEN Environment `AWS_ACTUAL`
- WHEN Ansible runs
- THEN the extra-var is the SSM bucket

### Requirement: Academy caller stays Vocareum-only
`rest-api-cd-academy-caller.yml` SHALL fail if `aws_environment` is not `academy`.
