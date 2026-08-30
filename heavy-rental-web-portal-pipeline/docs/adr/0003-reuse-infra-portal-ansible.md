# ADR 0003: Reuse infra portal Ansible (copy, do not fork)

- **Status:** Accepted
- **Date:** 2026-08-17
- **Branch:** portal CD branch 2 (`add-portal-cd-academy-deploy`)

## Context

`IMPLEMENTATION-PLAN.md` §2 / §6 requires `guest_base` + `portal` with `--limit portal`. Inventing a second nginx `/api` or compose file would drift from the estate `deploy-projects` / portal CD compose. Infra `apply` / `configure-only` do **not** compose portal.

The portal pipeline is copied into the React repo. A git submodule of the whole infra tree is heavier than the roles this CD needs.

## Decision

Copy estate `ansible/roles/guest_base` and `ansible/roles/portal` into `deploy-pipeline/ansible/`. Add a portal-only inventory (`asg-portal` only) and `playbooks/portal.yml`. Keep compose limits, `/api` proxy, and Stripe/PEM refusal identical to infra. `guest_base` maps `heavy-rental/portal` JSON to `/opt/heavy-rental/.env`. The portal role requires `REST_BASE_URL` on that file and does not read the React checkout `.env.api`.

Do not rewrite those roles. When estate compose or `guest_base` CloudWatch `daemon.json` (Docker Engine `awslogs` log-opts, not ECS `awslogs-stream-prefix`) changes, copy again.

## Consequences

- This CD can run without checking out the infra repo or a `GH_TOKEN`.
- Drift is possible if only one tree is updated — header comments point at the estate source.
- Inventory cannot accidentally play `rest` / `haystack` / `neo4j`.
