# Spec: haystack-cd-paid

## ADDED Requirements

### Requirement: Paid caller is OIDC-only
`haystack-cd-paid-caller.yml` SHALL NOT declare Vocareum key inputs. Environment SHALL be `AWS_ACTUAL`.

#### Scenario: Paid refuses academy
- GIVEN Environment `academy` on the paid caller
- THEN assert fails

### Requirement: Paid Ansible SSM bucket
Paid Haystack CD SHALL use `heavy-rental-ssm-<account>-actual` for Ansible SSM.

#### Scenario: Paid compose uses SSM bucket
- GIVEN Environment `AWS_ACTUAL`
- WHEN Ansible runs
- THEN the extra-var is the SSM bucket

### Requirement: Academy caller stays Vocareum-only
`haystack-cd-academy-caller.yml` SHALL fail if `aws_environment` is not `academy`.
