# Tasks: add-haystack-cd-academy-deploy

- [x] 1.1 Proposal, design, specs + scope amendment
- [x] 1.2 OpenSPDD + ADR 0003 + BOOTSTRAP
- [x] 2.1 Copy guest_base + haystack; haystack-only playbook
- [x] 2.2 resolve-image + ansible-haystack + SSM verify
- [x] 2.3 Update studies
- [x] 3.1 PREPARE-HAYSTACK-REPO.md (app not ready; env + sidecar contract)
- [x] 3.2 Alias SM Postgres names + Academy live flags on `.env`; `uv run` sidecars
- [x] 3.3 Overlay Haystack Environment Profile knobs onto guest `.env` only; keep `NEO4J_URI` / `NEO4J_POPULATE_URL` infra-owned; do not rebuild the image (ADR 0009)
- [x] 3.4 Spec/docs: academy vars ≠ image layers; full overlay key list matches YAML; BOOTSTRAP records that setting a Profile var does not change GHCR
