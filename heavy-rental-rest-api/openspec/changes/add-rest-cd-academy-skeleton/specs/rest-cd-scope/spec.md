# Delta for rest-cd-scope

**Superseded** for compose by [`../../../add-rest-cd-academy-deploy/specs/rest-cd-scope/spec.md`](../../../add-rest-cd-academy-deploy/specs/rest-cd-scope/spec.md). This file is the branch-1 fail-closed contract. Do **not** treat “compose is branch 2” or “deploy fails closed” as current behavior — `add-rest-cd-academy-deploy` delivered compose.

## ADDED Requirements

### Requirement: No compose or Terraform on this branch
`action=deploy` and `action=configure-only` SHALL fail closed before Ansible or image pull. This workflow SHALL NOT run Terraform. It SHALL NOT play Ansible groups `portal`, `haystack`, or `neo4j`.

#### Scenario: Deploy waits for branch 2
- GIVEN the operator selects `deploy` or `configure-only`
- WHEN the workflow runs
- THEN assert-lab and discover may succeed
- AND a job fails stating compose is branch 2
- AND no `docker` or `ansible-playbook` runs
