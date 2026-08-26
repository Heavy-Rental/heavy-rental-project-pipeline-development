# Design: REST CD Academy skeleton

**Superseded** for compose and verify by [`../add-rest-cd-academy-deploy/`](../add-rest-cd-academy-deploy/) and for paid/OIDC by [`../add-rest-cd-paid-deploy/`](../add-rest-cd-paid-deploy/). Keep this file as the branch-1 record. Do not treat “verify is discover-only” or “compose is branch 2” as current behavior.

## Context

Study `REST-API-CD-FEASIBILITY.md` §5 / `IMPLEMENTATION-PLAN.md` §5. Infra `HR-162` already composes REST. This repo’s Release pipeline builds `ghcr.io/<owner>/heavy_rental_rest_api:<tag>` (Publish on `workflow_dispatch`) and a `.tar.gz` artifact.

## Decisions

1. Academy caller only. Environment must be `academy`. (Paid is a later change; the reusable later accepts `AWS_ACTUAL`.)
2. Vocareum keys from `$GITHUB_EVENT_PATH` or Environment `academy`. Mask. Never interpolate `${{ inputs.aws_* }}`.
3. Discover `asg-rest` via AWS API. No instance-ID inputs. Do not print instance IPs or the internal REST ALB URL.
4. Compose / GHCR pull is branch 2. `verify` on this branch is discover-only (no `GET :8080`).

## Risks

- Vocareum token expired → `sts` fails; paste a fresh token.
- ASG desired=0 → discover fails; use infra CD, not this workflow.
