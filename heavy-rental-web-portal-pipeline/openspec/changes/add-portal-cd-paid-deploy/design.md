# Design: Portal CD paid

Match infra ADR 0017: two callers, one job graph. Environment `AWS_ACTUAL` (not feasibility `paid`). Auth via `resolve-aws-profile`. Paid Ansible S3 is the SSM transfer bucket.

Non-goals: duplicate 400-line YAML, tfstate write on guests, mobile.
