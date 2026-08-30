# ADR 0003: Reuse infra Haystack Ansible (copy, do not fork)

- **Status:** Accepted
- **Date:** 2026-08-17
- **Change:** `add-haystack-cd-academy-deploy`

## Context

`IMPLEMENTATION-PLAN.md` §6 requires `guest_base` + `haystack` with `--limit haystack`. A second compose file would drift from estate first-compose (`deploy-projects` / `site.yml`, not infra `apply`). Worker runtime is [ADR 0011](0011-devcontainer-worker-sidecars.md) / infra ADR 0020.

## Decision

Copy estate `guest_base` and `haystack` into `deploy-pipeline/ansible/`. Inventory is `asg-haystack` only. Keep limits and the no-neo4j check identical.

## Consequences

- CD can run without checking out the infra repo.
- Copy again when estate compose or `guest_base` CloudWatch `daemon.json` (Docker Engine `awslogs` log-opts, not ECS `awslogs-stream-prefix`) changes.
