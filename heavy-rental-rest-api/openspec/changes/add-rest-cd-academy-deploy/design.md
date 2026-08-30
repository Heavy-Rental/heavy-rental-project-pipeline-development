# Design: REST CD Academy deploy

## Context

Study `REST-API-CD-FEASIBILITY.md` §8 / `IMPLEMENTATION-PLAN.md` §6. As-built: infra `apply` / `configure-only` do **not** compose REST; first-compose is infra `deploy-projects` (`site.yml`) or this app CD (`guest_base` + `rest`, Tomcat `:8080`, `1g` / `1.0`). Branch 1 discovers `asg-rest`. This change re-runs that playbook from REST CD. The REST ALB is internet-facing `:8080`. `APP_CORS_ALLOWED_ORIGINS` in `heavy-rental/rest` is for **direct** REST ALB browser calls; portal nginx `/api` omits `Origin` (infra ADR 0018).

## Decisions

1. **Copy, do not rewrite.** `deploy-pipeline/ansible/roles/{guest_base,rest}` are copies of the estate roles. Rest-only inventory and `playbooks/rest.yml` wrap them. `--limit rest`.
2. **Image is a pipeline extra-var.** `resolve-image` (deploy only) requires a registry/compose tag (`image_ref` / `REST_IMAGE`) and MAY pass `image_http_url` for `docker load`. A tar URL does not replace the tag. Empty deploy **and** empty configure-only fail — no stock Tomcat.
3. **Public GHCR or ECR or tar.** Unauthenticated GHCR probe: 401/403 → fail. Guest `LabRole` logs in to ECR. No PAT on the guest.
4. **SSM plugin bucket** is `heavy-rental-tfstate-${ACCOUNT}-academy`.
5. **Verify** is SSM `GET :8080/actuator/health` (**2xx** only; same as ALB `tg-rest` matcher `200-299`). 401 on `/` is not healthy. Do not fail solely because Haystack is down. Do not print instance IPs or `REST_BASE_URL`.

## Risks

- Drift if estate `guest_base` / `rest` change and this copy is not updated.
- `deploy` with an old tag does not pull (`compose up` is not `--pull always`).
- Expired Vocareum token still fails at `sts` before Ansible.
