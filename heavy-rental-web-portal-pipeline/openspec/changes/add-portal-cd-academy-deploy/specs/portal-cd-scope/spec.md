# Delta for portal-cd-scope

## MODIFIED Requirements

### Requirement: No Terraform; portal group only
This workflow SHALL NOT run Terraform, create `asg-portal`, or run `stop` / `destroy`. It SHALL NOT play Ansible groups `rest`, `haystack`, or `neo4j`. `action=deploy` and `action=configure-only` SHALL run portal compose (branch 2). They SHALL NOT fail closed with a “wait for branch 2” message. `configure-only` SHALL NOT run `npm`, `vite`, or `docker build`.

#### Scenario: Deploy composes portal
- GIVEN the operator selects `deploy` or `configure-only`
- AND assert-lab and discover succeed
- WHEN the workflow runs
- THEN ansible-portal runs `guest_base` + `portal` only
- AND no job runs `terraform`

#### Scenario: Verify does not compose
- GIVEN the operator selects `verify`
- WHEN the workflow runs
- THEN ansible-portal is skipped
- AND verify still runs SSM `GET /`

#### Scenario: configure-only does not build the SPA
- GIVEN `action=configure-only`
- WHEN the workflow finishes
- THEN no job ran `npm ci`, `npm run build`, or `vite build`
