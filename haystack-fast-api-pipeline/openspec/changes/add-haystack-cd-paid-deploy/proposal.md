# Proposal: Haystack CD paid deploy

**Status:** Delivered (`haystack-cd-paid-caller.yml`).

Haystack CD was Academy-only. Infra paid already creates `asg-haystack`. Add an OIDC paid caller (Environment `AWS_ACTUAL`), share reusable jobs, SSM bucket not tfstate. No neo4j service. No Terraform.
