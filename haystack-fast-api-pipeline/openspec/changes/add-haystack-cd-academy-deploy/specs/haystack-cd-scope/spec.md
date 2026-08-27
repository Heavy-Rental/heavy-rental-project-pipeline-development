# Delta for haystack-cd-scope

## MODIFIED Requirements

### Requirement: No Terraform; haystack group only
This workflow SHALL NOT run Terraform or `stop` / `destroy`. It SHALL NOT play portal / rest / neo4j. `deploy` / `configure-only` SHALL compose Haystack. They SHALL NOT fail closed with “wait for branch 2.”

#### Scenario: Deploy composes Haystack
- THEN ansible-haystack runs `guest_base` + `haystack` only
- AND no `neo4j` service starts

#### Scenario: Verify does not compose
- THEN ansible-haystack is skipped
- AND verify still runs SSM `GET :8000/health` (2xx)
