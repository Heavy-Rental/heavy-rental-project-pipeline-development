# Design: Haystack CD Academy skeleton

## Context

Study `HAYSTACK-CD-FEASIBILITY.md` §5 / `IMPLEMENTATION-PLAN.md` §5. Infra `HR-162` already composes Haystack. This repo’s Release pipeline builds `ghcr.io/<owner>/haystack_recommender:<tag>` (off PR) and a `.tar.gz` artifact.

## Decisions

1. Academy only. Environment must be `academy`.
2. Vocareum keys from `$GITHUB_EVENT_PATH` or Environment `academy`. Mask. Never interpolate `${{ inputs.aws_* }}`.
3. Discover `asg-haystack` via AWS API. No instance-ID inputs. Do not print instance IPs or the internal Haystack ALB URL.
4. Compose / GHCR pull is branch 2. `verify` on this branch is discover-only (no `GET :8000`).

## Risks

- Vocareum token expired → `sts` fails; paste a fresh token.
- ASG desired=0 → discover fails; use infra CD, not this workflow.
