# Delta for rest-cd-scope

## MODIFIED Requirements

### Requirement: No Terraform; rest group only
This workflow SHALL NOT run Terraform, create `asg-rest`, or run `stop` / `destroy`. It SHALL NOT play Ansible groups `portal`, `haystack`, or `neo4j`. `action=deploy` and `action=configure-only` SHALL run REST compose (branch 2). They SHALL NOT fail closed with a “wait for branch 2” message.

#### Scenario: Deploy composes REST
- GIVEN the operator selects `deploy` or `configure-only`
- AND assert-lab and discover succeed
- WHEN the workflow runs
- THEN ansible-rest runs `guest_base` + `rest` only
- AND no job runs `terraform`

#### Scenario: Verify does not compose
- GIVEN the operator selects `verify`
- WHEN the workflow runs
- THEN ansible-rest is skipped
- AND verify still runs SSM `GET :8080`
