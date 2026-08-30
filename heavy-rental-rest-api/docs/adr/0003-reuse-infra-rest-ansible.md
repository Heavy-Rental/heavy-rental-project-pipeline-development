# ADR 0003: Reuse infra REST Ansible (copy, do not fork)

- **Status:** Accepted
- **Date:** 2026-08-17
- **Change:** `add-rest-cd-academy-deploy`

## Context

`IMPLEMENTATION-PLAN.md` §2 / §6 requires `guest_base` + `rest` with `--limit rest`. Inventing a second compose file would drift from the estate `deploy-projects` / REST CD compose. Infra `apply` / `configure-only` do **not** compose REST.

## Decision

Copy estate `ansible/roles/guest_base` and `ansible/roles/rest` into `deploy-pipeline/ansible/`. Add a rest-only inventory (`asg-rest` only) and `playbooks/rest.yml`. Keep compose limits (`1g` / `1.0`, `:8080`) identical to infra. Keep `guest_base` CloudWatch `daemon.json` in sync (Docker Engine `awslogs` log-opts, not ECS `awslogs-stream-prefix`).

## Consequences

- This CD can run without checking out the infra repo.
- Drift is possible if only one tree is updated — header comments point at the estate source.
- Inventory cannot accidentally play `portal` / `haystack` / `neo4j`.
