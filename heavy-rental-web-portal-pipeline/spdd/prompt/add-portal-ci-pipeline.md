# REASONS Canvas: add-portal-ci-pipeline

**Input analysis:** [add-portal-ci-pipeline.md](../analysis/add-portal-ci-pipeline.md)  
**Behavior contract:** [OpenSpec change](../../openspec/changes/add-portal-ci-pipeline/)

When reality diverges, fix this prompt first — then update the YAML.

---

## R — Requirements

- Three-pipeline GitHub Flow family for the React portal.
- Fast Feedback: Integration only.
- Integration CI: Assert caller → Integration → (QC ∥ Security ∥ CodeQL ∥ REST Endpoint Tests) → GitHub Flow CI Gate.
- Release: same gates except REST Endpoint Tests, plus Packaging (`npm run build` without `VITE_*` lab URLs, `dist/` zip, nginx try_files image, GHCR off PR). Scan `dist/` and the image for secrets / localhost:8080|8000. CD mounts `/api`.
- Node 22 + `npm ci`. No GitHub Environment secrets for v1 CI.
- Authoring path: `heavy-rental-web-portal-pipeline/integration_pipeline/`.
- This family stops at packaging. Academy CD is `deploy-pipeline/`.

## E — Entities

Artifacts:

| Name | Source |
| --- | --- |
| Lock fingerprint | `package.json`, `package-lock.json` |
| SARIF | Semgrep, npm-audit, Trivy |
| Release zip | `dist/` contents |
| Release image tar | `heavy-rental-web-portal-v{version}-build{run}-{sha}.tar.gz` |
| GHCR | `ghcr.io/{owner}/heavy-rental-web-portal:{tag}` (not on pull_request) |

## A — Approach

- Keep existing YAML. New work is OpenSpec + SPDD + ADR + `specification/` + PREPARE.
- `DEFAULT_APP_REPOSITORY`: `SA62-team1/heavy-rental-react-web-portal` (act).

## S — Structure

```
heavy-rental-web-portal-pipeline/
  specification/
  openspec/
  spdd/
  docs/adr/
  fast-feedback-ci-pipeline/
  integration_pipeline/     # underscore
  release-pipeline/
  deploy-pipeline/
```

Job `name:` values:

- `Assert caller`
- `Integration`
- `Quality Control`
- `Security Testing`
- `CodeQL Analysis`
- `REST Endpoint Tests` (Integration CI only)
- `GitHub Flow CI Gate`
- `Packaging` (release only)

## O — Operations

1. Document OpenSpec + OpenSPDD + ADRs (this change).
2. Do not add jobs.
3. Keep `actionlint` paths pointed at `integration_pipeline/`.

## N — Norms

- Header comments on YAML.
- `set -euo pipefail` on multi-line `run:`.
- Bind `github.*` / `inputs.*` through `env:` inside `run:`.
- SARIF is the security report standard.

## S — Safeguards (negative space)

- **DO NOT** apply Terraform or compose onto `asg-portal` in this family.
- **DO NOT** call a live Spring / Haystack URL from CI.
- **DO NOT** pass `VITE_*` REST/Haystack/API URLs or `STRIPE_API_KEY` (`sk_`) into Release `npm run build`.
- **DO NOT** bake `REST_BASE_URL` / `VITE_*` / `STRIPE_` / `AWS_` into the nginx image (`ENV`/`ARG`/`COPY .env`/`--build-arg`).
- **DO NOT** generate nginx `proxy_pass` to a hostname in the Release image (CD mounts `/api`).
- **DO NOT** fail REST Endpoint Tests solely because mock scripts are missing.
- **DO NOT** `docker push` on pull_request events.
- **DO NOT** put `on: push` on reusable files.
- **DO NOT** use Java, Maven, uv, or Android SDK as the app toolchain.
- **DO NOT** cancel in-progress Release runs.
- **DO NOT** rename `integration_pipeline/` as part of this documentation change.
