# Changelog

## Unreleased

### Changed

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
