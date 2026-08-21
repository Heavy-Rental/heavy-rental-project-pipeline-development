# Proposal: Haystack CD paid deploy

Haystack CD is Academy-only. Infra paid already creates `asg-haystack`. Add an OIDC paid caller (Environment `AWS_ACTUAL`), share reusable jobs, SSM bucket not tfstate. No neo4j service. No Terraform.
