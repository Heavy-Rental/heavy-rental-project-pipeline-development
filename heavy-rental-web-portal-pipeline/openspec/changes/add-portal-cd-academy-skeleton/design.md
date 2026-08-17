# Design: Portal CD Academy skeleton

## Context

Study `WEB-PORTAL-CD-FEASIBILITY.md` §5 / `IMPLEMENTATION-PLAN.md` §5. Infra `HR-162` already composes portal. This repo’s Release pipeline builds the image (`ghcr.io/<owner>/heavy-rental-web-portal:<tag>` off PR) and a `.tar.gz` artifact.

## Decisions

1. Academy only. Environment must be `academy`.
2. Vocareum keys from `$GITHUB_EVENT_PATH` or Environment `academy`. Mask. Never interpolate `${{ inputs.aws_* }}`.
3. Discover `asg-portal` via AWS API. No instance-ID inputs.
4. Compose / GHCR pull is branch 2. `verify` on this branch is discover-only (no `GET /`).

## Risks

- Vocareum token expired → `sts` fails; paste a fresh token.
- ASG desired=0 → discover fails; use infra CD, not this workflow.
