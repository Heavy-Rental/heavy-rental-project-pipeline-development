# SPDD Analysis: add-portal-cd-paid-deploy

Portal CD cannot target the billed estate. Infra paid already creates `asg-portal`. Add an OIDC caller; keep academy Vocareum-only; share jobs; SSM bucket not tfstate.

Safeguards: no Vocareum keys on paid YAML; no `secrets: inherit` (OIDC via `vars.AWS_ROLE_TO_ASSUME`); academy caller refuses `AWS_ACTUAL`; guests never `s3:PutObject` on estate state.
