# Delta for haystack-cd-scope

**Superseded** for compose by [`../../../add-haystack-cd-academy-deploy/specs/haystack-cd-scope/spec.md`](../../../add-haystack-cd-academy-deploy/specs/haystack-cd-scope/spec.md).

## ADDED Requirements

### Requirement: No compose or Terraform on this branch
`action=deploy` and `action=configure-only` SHALL fail closed before Ansible or image pull. This workflow SHALL NOT run Terraform. It SHALL NOT play Ansible groups `portal`, `rest`, or `neo4j`. It SHALL NOT start a `neo4j` container.

#### Scenario: Deploy waits for branch 2
- GIVEN the operator selects `deploy` or `configure-only`
- WHEN the workflow runs
- THEN assert-lab and discover may succeed
- AND a job fails stating compose is branch 2
- AND no `docker` or `ansible-playbook` runs
