# Delta for portal-cd-scope

## ADDED Requirements

### Requirement: No compose or Terraform on this branch
`action=deploy` and `action=configure-only` SHALL fail closed before Ansible or image pull. This workflow SHALL NOT run Terraform.

#### Scenario: Deploy waits for branch 2
- GIVEN the operator selects `deploy` or `configure-only`
- WHEN the workflow runs
- THEN assert-lab and discover may succeed
- AND a job fails stating compose is branch 2
- AND no `docker` or `ansible-playbook` runs
