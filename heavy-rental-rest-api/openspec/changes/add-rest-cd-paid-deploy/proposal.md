# Proposal: REST CD paid deploy

REST CD is Academy-only. Infra paid already creates `asg-rest`. Add an OIDC paid caller (Environment `AWS_ACTUAL`), share reusable jobs, SSM bucket not tfstate. Academy caller stays Vocareum-only. No Terraform.
