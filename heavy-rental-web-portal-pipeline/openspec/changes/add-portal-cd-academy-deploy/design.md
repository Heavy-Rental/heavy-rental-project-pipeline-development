# Design: Portal CD Academy deploy

## Context

Study `WEB-PORTAL-CD-FEASIBILITY.md` §8 / `IMPLEMENTATION-PLAN.md` §6. Infra `HR-162` already first-composes portal (`guest_base` + `portal`, `/api` → `REST_BASE_URL`). Branch 1 discovers `asg-portal`. This change re-runs that playbook from portal CD.

## Decisions

1. **Copy, do not rewrite.** `deploy-pipeline/ansible/roles/{guest_base,portal}` are copies of the estate roles. Portal-only inventory and `playbooks/portal.yml` wrap them. `--limit portal`.
2. **Image is a pipeline extra-var.** `resolve-image` (deploy only) chooses `image_http_url` or a registry tag. Ansible does not invent GHCR URLs. Empty deploy fails (no silent stock `nginx`). configure-only may use `vars.PORTAL_IMAGE` or stock `nginx`.
3. **Public GHCR or ECR or tar.** Unauthenticated GHCR probe: 401/403 → fail (copy to ECR or use `image_http_url`). Guest `LabRole` logs in to ECR. No PAT on the guest.
4. **SSM plugin bucket** is the lab state bucket `heavy-rental-tfstate-${ACCOUNT}-academy` (same as infra).
5. **Verify** is SSM `curl http://127.0.0.1/` (200–302) on every InService + SSM Online guest. Do not fail solely because `/api` is down.
6. **No Vite overlay.** `/api` is SM `REST_BASE_URL` (AWS). GitHub `VITE_*` does not reconfigure the React bundle (ADR 0008).
7. **Three stores for configure-only / deploy.** GitHub `academy` = Vocareum + `PORTAL_IMAGE` / `IMAGE_HTTP_URL` + `VITE_STRIPE_PUBLISHABLE_KEY`. Guest `/opt/heavy-rental/.env` = SM `heavy-rental/portal` then optional academy `pk_` overlay (`REST_BASE_URL` required). App Vite dotenv = Release only — CD does not read `.env.api`.

## Risks

- Drift if estate `guest_base` / `portal` change and this copy is not updated.
- `deploy` with an old tag does not pull (`compose up` is not `--pull always`).
- Expired Vocareum token still fails at `sts` before Ansible.
