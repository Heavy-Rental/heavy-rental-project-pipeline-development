# Design: Portal CD Academy skeleton

**Superseded** for compose and verify by [`../add-portal-cd-academy-deploy/`](../add-portal-cd-academy-deploy/) and for paid/OIDC by [`../add-portal-cd-paid-deploy/`](../add-portal-cd-paid-deploy/). Keep this file as the branch-1 record. Do not treat “verify is discover-only” or “compose is branch 2” as current behavior. As-built first-compose is infra `deploy-projects` or this app CD (not infra `apply`). This repo’s Release pipeline builds the image (`ghcr.io/<owner>/heavy_rental_web_portal:<semver>` via dispatch-only Publish after DAST) and `heavy_rental_web_portal-image.tar.gz`. The REST ALB is internet-facing `:8080`.

## Context

Study `WEB-PORTAL-CD-FEASIBILITY.md` §5 / `IMPLEMENTATION-PLAN.md` §5. Keep this file as the branch-1 record.

## Decisions

1. Academy only. Environment must be `academy`.
2. Vocareum keys from `$GITHUB_EVENT_PATH` or Environment `academy`. Mask. Never interpolate `${{ inputs.aws_* }}`.
3. Discover `asg-portal` via AWS API. No instance-ID inputs.
4. Compose / GHCR pull is branch 2. `verify` on this branch is discover-only (no `GET /`).

## Risks

- Vocareum token expired → `sts` fails; paste a fresh token.
- ASG desired=0 → discover fails; use infra CD, not this workflow.
