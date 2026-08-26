# REASONS Canvas: add-rest-ci-pipeline

**Input analysis:** [add-rest-ci-pipeline.md](../analysis/add-rest-ci-pipeline.md)  
**Behavior contract:** [OpenSpec change](../../openspec/changes/add-rest-ci-pipeline/)

When reality diverges, fix this prompt first — then update the YAML.

---

## R — Requirements

- Three-pipeline GitHub Flow family for the Spring REST API.
- Fast Feedback: Integration only, feature-branch pushes (ignore `master`/`develop`). No `pull_request` trigger.
- Integration CI: PR/push `develop` + `workflow_dispatch`. Jobs: Assert caller → Integration → (QC ∥ Security ∥ CodeQL) → GitHub Flow CI Gate.
- Release: `workflow_dispatch` only (creates the GitHub Release; do not use `on: release`). Jobs: Assert caller → Integration (checkout `master`) → QC → Packaging → DAST → Publish. No Security Testing or CodeQL on Release. Image is env-driven: refuse baked `POSTGRES_*` / `SPRING_DATASOURCE_*` / `HAYSTACK_*` / `STRIPE_*` / `APP_JWT_*`; prove dummy runtime env. Do not `COPY` `spring-datasource.env` into the image. Publish (not Packaging) pushes GHCR and `gh release create`.
- Java 21 Temurin + `./mvnw`. QC starts Docker `postgres:16-alpine`.
- Integration QC secrets: `REST_API_DB_*` / Environment `integration`.
- Release QC secrets: same `REST_API_DB_*` names / Environment `production`. `REST_API_DB_URL` is derived.
- Specs live under `heavy-rental-rest-api/`.
- This family stops at packaging. Academy CD is `deploy-pipeline/`.

## E — Entities

```mermaid
classDiagram
    class CallerWorkflow
    class ReusableWorkflow
    class IntegrationJob
    class QualityControlJob
    class SecurityTestingJob
    class CodeQLJob
    class PackagingJob
    class DastJob
    class PublishJob
    class GitHubFlowGateJob
    CallerWorkflow --> ReusableWorkflow : uses
    ReusableWorkflow --> IntegrationJob
    IntegrationJob --> QualityControlJob
    IntegrationJob --> SecurityTestingJob
    IntegrationJob --> CodeQLJob
    QualityControlJob --> GitHubFlowGateJob
    QualityControlJob --> PackagingJob
    PackagingJob --> DastJob
    DastJob --> PublishJob
```

Artifacts:

| Name | Source |
| --- | --- |
| Maven fingerprint | `pom.xml` |
| Test reports | surefire / failsafe |
| SARIF | `security-reports/semgrep.sarif`, `security-reports/trivy-fs.sarif` |
| Combined security PDF | `security-combined-report-pdf` (Integration CI) |
| Release WAR | versioned `heavy-rental-rest-api-v{version}-build{run}-{sha}.war` + stable copy |
| Release image tar | `heavy_rental_rest_api-image.tar.gz` |
| GHCR | `ghcr.io/{owner}/heavy_rental_rest_api:{x.y.z}` and `:latest` (Publish on dispatch) |
| Combined DAST PDF | `dast-combined-report-pdf` |
| Cloud JDBC env | `release-deploy-config/spring-datasource.env` (no password) |

## A — Approach

- Keep existing YAML. New work is OpenSpec + SPDD + ADR + `specification/`.
- Fast Feedback / Integration CI `DEFAULT_APP_REPOSITORY`: `SA62-team1/heavy-rental-spring-rest-api` (act). Release: `Heavy-Rental/heavy-rental-spring-rest-api`. Installed Fast Feedback / CI callers check out the calling commit; Release always checks out `master`.

## S — Structure

```
heavy-rental-rest-api/
  specification/
  openspec/
  spdd/
  docs/adr/
  fast-feedback-ci-pipeline/
  integration-pipeline/
  release-pipeline/
  deploy-pipeline/          # CD family — not this canvas
```

Job `name:` values (branch protection):

- `Assert caller`
- `Integration`
- `Quality Control`
- `Security Testing`
- `CodeQL Analysis`
- `GitHub Flow CI Gate`
- `Packaging` (release only)
- `DAST` (release only)
- `Publish` (release only)

## O — Operations

1. Document OpenSpec + OpenSPDD + ADRs (this change).
2. Do not add jobs.
3. `actionlint` the six CI files if YAML is later edited.

## N — Norms

- `# ====...====` headers on YAML.
- `set -euo pipefail` on multi-line `run:`.
- No `secrets: inherit` on **CI** callers (paid CD does inherit; that is a different family).
- No `environment:` on caller `uses:` jobs.
- Bind `github.*` / `inputs.*` through `env:` inside `run:`.
- SARIF is the security report standard.

## S — Safeguards (negative space)

- **DO NOT** apply Terraform or compose onto `asg-rest` in this family.
- **DO NOT** treat `REST_API_DB_*` as guest SM (`heavy-rental/rest`).
- **DO NOT** require `REST_API_CLOUD_DB_*` or `REST_API_DB_URL` as secrets.
- **DO NOT** bake `POSTGRES_*`, `SPRING_DATASOURCE_*`, `HAYSTACK_*`, `STRIPE_*`, `APP_JWT_*`, or `REST_API_*` into the Release image (`ENV`/`ARG`/`COPY .env`/`--build-arg`).
- **DO NOT** `COPY` `spring-datasource.env` into the image.
- **DO NOT** require `REST_API_DB_URL` as a secret.
- **DO NOT** subscribe the Release caller to `pull_request` or `on: release` (dispatch only; Publish creates the GitHub Release).
- **DO NOT** `docker push` from Packaging (Publish does).
- **DO NOT** put `on: push` on reusable files.
- **DO NOT** use Python/uv, Node, or Android SDK as the app toolchain.
- **DO NOT** cancel in-progress Release runs.
- **DO NOT** change Haystack, portal, or mobile pipelines in this change.
