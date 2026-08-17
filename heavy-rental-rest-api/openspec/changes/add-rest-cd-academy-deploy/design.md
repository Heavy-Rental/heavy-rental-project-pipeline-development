# Design: REST CD Academy deploy

## Context

Study `REST-API-CD-FEASIBILITY.md` §8 / `IMPLEMENTATION-PLAN.md` §6. Infra `HR-162` already first-composes REST (`guest_base` + `rest`, Tomcat `:8080`, `1g` / `1.0`). Branch 1 discovers `asg-rest`. This change re-runs that playbook from REST CD.

## Decisions

1. **Copy, do not rewrite.** `deploy-pipeline/ansible/roles/{guest_base,rest}` are copies of the estate roles. Rest-only inventory and `playbooks/rest.yml` wrap them. `--limit rest`.
2. **Image is a pipeline extra-var.** `resolve-image` (deploy only) chooses `image_http_url` or a registry tag (`image_ref` / `REST_IMAGE`). Empty deploy **and** empty configure-only fail — no stock Tomcat.
3. **Public GHCR or ECR or tar.** Unauthenticated GHCR probe: 401/403 → fail. Guest `LabRole` logs in to ECR. No PAT on the guest.
4. **SSM plugin bucket** is `heavy-rental-tfstate-${ACCOUNT}-academy`.
5. **Verify** is SSM `GET :8080/actuator/health` or `/` (200–302, or 401/403 if Tomcat is up). Do not fail solely because Haystack is down. Do not print instance IPs or `REST_BASE_URL`.

## Risks

- Drift if estate `guest_base` / `rest` change and this copy is not updated.
- `deploy` with an old tag does not pull (`compose up` is not `--pull always`).
- Expired Vocareum token still fails at `sts` before Ansible.
