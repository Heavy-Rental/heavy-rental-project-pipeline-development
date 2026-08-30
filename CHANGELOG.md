# Changelog

## Unreleased

### Changed

- Fourth spec/docs consistency pass: Haystack OpenSpec DAST now matches YAML (ZAP + Dastardly gates; Nuclei report-only). Haystack OpenSpec context names `populate-neo4j-from-haystack.sh`. Skeleton SPDD fail-closed is marked historical. ADR titles no longer read as “Release ends at the tar.” Family indexes document Security Report schedules and Fast Feedback wait-if-in-flight. Paid CD `secrets: inherit` is stated per family (Haystack/REST yes, portal no). Feasibility operator checklists use Environment `AWS_ACTUAL` (not `paid`), tell operators to copy live YAML (not fail-closed stubs), and empty `image_ref` is not `:latest`. AWS study paid ASCII matches internet-facing REST ALB `:8080` and two NAT Gateways. Portal nginx `/api` snippet matches guest `proxy_pass` without a trailing URI and `Host $proxy_host`. Root README: copy from family folders, not this repo’s `.github/workflows/` copies.

- Third spec/docs consistency pass against YAML: GitHub Flow now documents Fast Feedback **wait-if-in-flight** on every family (Haystack walkthrough, OpenSpec, SPDD, and the root index; mobile README/walkthrough). Haystack workers are named as `postgres:17` + `sync-from-primary.sh` and `python:3.12-slim` + `populate-neo4j-from-haystack.sh` (wraps `populate_neo4j.py`). REST and portal family READMEs include Security Report schedules (Monday 06:00 / 08:00 UTC). Checkout docs no longer treat unused `DEFAULT_APP_REPOSITORY` as a runtime default. Nuclei is documented as DAST report-only. Security Report callers no longer claim Release uploads SARIF. Portal BOOTSTRAP/PREPARE distinguish academy Run-form Vocareum keys from “do not bake keys”. Feasibility studies no longer present stale current facts: REST CD sequence is `configure.yml` then `deploy-projects`/app CD (not apply first-compose); portal CD body matches internet-facing REST ALB and Release Packaging Environment `academy` for Stripe `pk_`; AWS study inventory, Well-Architected, isolation, and paid Environment names match as-built (`AWS_ACTUAL`, two NAT Gateways, public REST ALB `:8080`). Example CD stubs no longer say infra Ansible first-composes the three apps.

- Portal spec/docs aligned with YAML: restored `docs/samples/.env.production` (Release **scan** input; `vite build --mode api` loads `.env.api`). GitHub `VITE_STRIPE_PUBLISHABLE_KEY` (`pk_`) overlays guest `.env` on academy **and** `AWS_ACTUAL` and does not reconfigure the SPA. `resolve-image` requires a compose tag (a tar URL does not replace it). Skeleton OpenSpec fail-closed is marked historical. ADR 0004 install list is six GitHub Flow YAML files plus the Security Report pair. PREPARE is a checklist, not live inventory.

- REST spec/docs aligned with YAML: both Integration and Release callers pass an explicit `REST_API_DB_*` map from Repository secrets (QC still uses Environments `integration` / `production`). PREPARE is a checklist, not live inventory. BOOTSTRAP no longer treats a tar URL as a substitute for `REST_IMAGE` / `image_ref`. CD Environment tables include pricing overlay on academy **and** `AWS_ACTUAL`. Integration Check wait-for-in-flight Fast Feedback is documented. Skeleton OpenSpec fail-closed is marked historical.

- Haystack spec/docs aligned with YAML: the Security Report pair is documented as reporting-only (Monday 06:00 UTC; not a merge gate). ADR 0008 no longer says compose workers reuse the Release image (ADR 0011: `postgres:17` / `python:3.12-slim`). Semgrep publish is SARIF-only (`semgrep.json` / `semgrep.txt` not required). Integration CI `checks: write` and Release `contents: write` match the orchestration spec. SPDD CodeQL pin is `v4.37.8`. PREPARE “not ready” is a dated snapshot, not “today”.

- Pipeline-development root README and `specification/README.md` now match the family YAML: GitHub Flow reuses Fast Feedback on PR; first-compose is infra `deploy-projects` or app CD; GHCR names; REST ALB internet-facing `:8080`; Haystack workers (ADR 0011 / infra ADR 0020); Security Report is not a merge gate. Family indexes (Haystack, REST, portal) state the same first-compose and health facts.

- Haystack spec/docs verification against YAML: compose workers are `postgres:17` + `sync-from-primary.sh` and `python:3.12-slim` + `populate-neo4j-from-haystack.sh` (wraps `populate_neo4j.py`; ADR 0011; not uvicorn `-m`). Worker credential aliases (`SOURCE_USER`, `PG*`, `NEO4J_POPULATE_TRIGGER_URL`) match Ansible. First-compose is infra `deploy-projects` or app CD. CI `DEFAULT_APP_REPOSITORY` is `Heavy-Rental/haystack-fast-api`; Packaging tar is `haystack_recommender-image.tar.gz`. Profile overlay applies on Environment `academy` or `AWS_ACTUAL`.

- Portal spec/docs verification against YAML: Fast Feedback, Integration CI, and Release `DEFAULT_APP_REPOSITORY` is `Heavy-Rental/heavy-rental-react-web-portal`. Security Report pair is documented as reporting-only (not a merge gate; Monday 08:00 UTC). Paid portal CD does not `secrets: inherit` (OIDC via `vars.AWS_ROLE_TO_ASSUME`). Semgrep Publish SARIF is SARIF-only. GHCR is dispatch-only Publish (`heavy_rental_web_portal-image.tar.gz`). First-compose is infra `deploy-projects` or app CD. PREPARE includes Environment `AWS_ACTUAL`.

- REST spec/docs verification against YAML: Integration CI `DEFAULT_APP_REPOSITORY` is `Heavy-Rental/...` (Fast Feedback remains `SA62-team1/...` act fallback). Semgrep Publish SARIF is SARIF-only. Security Report pair is documented as reporting-only (not a merge gate). GHCR is dispatch-only Publish (`heavy_rental_rest_api-image.tar.gz`). REST ALB is internet-facing (do not call it internal). First-compose is infra `deploy-projects` or app CD. PREPARE includes Environment `AWS_ACTUAL`.

- Second spec/docs verification: REST and portal CD install lists now match YAML (`resolve-aws-profile` required; do not copy unused `resolve-vocareum-aws`). Haystack BOOTSTRAP academy vs `AWS_ACTUAL` secret tables no longer nest Vocareum keys under paid. ADR 0001 (Haystack/portal) binds the academy **caller**, not the shared reusable. OpenSpec academy-auth (Haystack/portal) amended the same way as REST. Semgrep living specs/walkthroughs are SARIF-only (no required `semgrep.json` / `semgrep.txt`). Haystack Release image tar is `haystack_recommender-image.tar.gz`. Portal CD walkthrough job names and `GET /` 200–302 vs ALB `200-399` match YAML. As-built tables cover first-compose (`deploy-projects`), portal Packaging Environment `academy` (`pk_`), and portal health matchers. Academy infra example stub no longer says “copy this file”. Broken Haystack CI study link (`../` → `../../`) fixed.

- Feasibility studies: as-built tables (`AWS_ACTUAL`, internet-facing REST ALB, GHCR names, dispatch-only Release, paid app CD delivered). Folder index at `cloud-deployment-feasibility-studies/README.md`. Example paid stubs default to Environment `AWS_ACTUAL`.

- Synced living specification and documentation with the YAML that already ships.
- Mobile OpenSpec / OpenSPDD / ADRs now match Mockoon-only Mock Contract Tests (fail if scripts missing; no Prism), `workflow_dispatch`-only Release, MobSF DAST, and GitHub Release Publish (no GHCR). SAST, CodeQL, and mocks stay on Integration CI.
- Added mobile ADRs 0006 (Mockoon-only) and 0007 (dispatch-only Release + MobSF).
- Replaced the root README template with a project index. `BLANK_README.md` remains the unused template copy.
- YAML header comments on mobile Release and Integration now match `on:` / job graphs (comment-only; no behavior change).

## v1.0.0

### Added

- Haystack, REST, portal, and mobile GitHub Actions families (Fast Feedback, Integration CI, Release).
- Haystack, REST, and portal Academy + paid app CD callers.
- OpenSpec, OpenSPDD, and ADR trees per family.
- Combined security PDF (Integration CI) and combined DAST PDF (Release).
