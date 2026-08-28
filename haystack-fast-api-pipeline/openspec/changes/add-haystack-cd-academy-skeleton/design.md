# Design: Haystack CD Academy skeleton

**Superseded** for compose and verify by [`../add-haystack-cd-academy-deploy/`](../add-haystack-cd-academy-deploy/) and for paid/OIDC by [`../add-haystack-cd-paid-deploy/`](../add-haystack-cd-paid-deploy/). Keep this file as the branch-1 record. Do not treat “verify is discover-only” or “compose is branch 2” as current behavior. As-built first-compose is infra `deploy-projects` or this app CD (not infra `apply`). Workers are [`../add-haystack-cd-workers/`](../add-haystack-cd-workers/) / [ADR 0011](../../../../docs/adr/0011-devcontainer-worker-sidecars.md).

## Context

Study `HAYSTACK-CD-FEASIBILITY.md` §5 / `IMPLEMENTATION-PLAN.md` §5. Keep this file as the branch-1 record. This repo’s Release pipeline builds `ghcr.io/<owner>/haystack_recommender:<tag>` (Publish after DAST) and `haystack_recommender-image.tar.gz`.

## Decisions

1. Academy only. Environment must be `academy`.
2. Vocareum keys from `$GITHUB_EVENT_PATH` or Environment `academy`. Mask. Never interpolate `${{ inputs.aws_* }}`.
3. Discover `asg-haystack` via AWS API. No instance-ID inputs. Do not print instance IPs or the internal Haystack ALB URL.
4. Compose / GHCR pull is branch 2. `verify` on this branch is discover-only (no `GET :8000`).

## Risks

- Vocareum token expired → `sts` fails; paste a fresh token.
- ASG desired=0 → discover fails; use infra CD, not this workflow.
