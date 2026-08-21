# Spec: portal-cd-paid

## ADDED Requirements

### Requirement: Paid caller is OIDC-only
`portal-cd-paid-caller.yml` SHALL NOT declare Vocareum key inputs. `aws_environment` SHALL be `AWS_ACTUAL`. Missing `AWS_ROLE_TO_ASSUME` or a set `AWS_ACCESS_KEY_ID` SHALL fail before compose.

#### Scenario: Paid refuses academy
- GIVEN Environment `academy` on the paid caller
- THEN assert fails and Ansible does not run

### Requirement: Paid Ansible SSM bucket
Paid portal CD SHALL pass `ansible_aws_ssm_bucket_name=heavy-rental-ssm-<account>-actual`. It SHALL NOT use the Terraform state bucket.

#### Scenario: Paid compose uses SSM bucket
- GIVEN Environment `AWS_ACTUAL` and a live OIDC session
- WHEN `action=deploy` runs Ansible
- THEN extra-var `ansible_aws_ssm_bucket_name` is the SSM bucket

### Requirement: Academy caller stays Vocareum-only
`portal-cd-academy-caller.yml` SHALL fail if `aws_environment` is not `academy`.

#### Scenario: AWS_ACTUAL on academy caller
- GIVEN Environment `AWS_ACTUAL` on the academy caller
- THEN assert fails
