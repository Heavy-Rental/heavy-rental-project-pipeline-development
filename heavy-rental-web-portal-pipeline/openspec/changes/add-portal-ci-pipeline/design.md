# Design: Web portal GitHub Actions CI family (as-implemented)

## Context

The React portal already has reusable-caller Fast Feedback, Integration CI, and Release workflows. Academy CD is a separate family. This document describes the CI family as the YAML behaves today.

Authoring path for Integration CI is `integration_pipeline/` (underscore).

## Goals / Non-Goals

**Goals:**

- Same GitHub Flow as REST / Haystack / mobile.
- Integration first; later jobs need Integration.
- Node 22 + npm ci + ESLint + `tsc`.
- REST endpoint tests against a local mock; skip-clean until scripts exist.
- Release artifacts consumable by Academy CD (`dist/` zip + nginx image; GHCR off PR).

**Non-Goals:**

- Changing existing YAML
- Hitting live Spring / Haystack from CI
- Terraform / compose / operate

## Decisions

1. **Reusable + caller gate.** Sole callers: `portal-fast-feedback-caller.yml`, `portal-ci-caller.yml`, `portal-release-caller.yml`.
2. **Node 22 + npm ci.** Integration verifies `package-lock.json` and `node_modules`.
3. **QC is lint + typecheck.** No Postgres, no GitHub Environment.
4. **REST Endpoint Tests skip-clean** when `package.json` lacks both a mock script (`mock:server` / `api:mock` / `start:mock`) and a test script (`test:api` / `test:endpoints` / `test:rest`). Mock binds `127.0.0.1:4010`.
5. **Release Packaging** runs `npm run build` **without** `VITE_*` REST/Haystack URLs, requires `dist/index.html` and at least one JS file, scans `dist/` for `sk_` / localhost:8080|8000, zips `dist/`, builds `nginx:1.27-alpine` with try_files only (no `proxy_pass` host), proves the image is static, pushes GHCR off PR (ADR 0007).
6. **CI family stops at packaging.** Compose and the `/api` proxy live in the CD family.

## Open Questions

None. This change documents shipped YAML.
