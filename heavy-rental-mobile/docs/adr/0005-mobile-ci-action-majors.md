# ADR 0005: Mobile CI pins current stable GitHub Action majors

- **Status:** Accepted
- **Date:** 2026-08-26
- **Change:** `add-mobile-ci-pipeline`

## Context

The first mobile YAML used older majors (`actions/checkout@v4`, `actions/setup-java@v4`, `android-actions/setup-android@v3`, `github/codeql-action@v3`, and peers). `setup-java@v4` is deprecated. REST and portal CI already float newer majors; Haystack SHA-pins exact commits (`actions/checkout@3d3c42e… # v7.0.1`).

Mobile needs a single pin policy so YAML, SPDD, and the human spec do not drift.

## Decision

Pin **floating major tags** (or the latest Trivy tag), not SHAs. Bump to the current stable set:

| Action | Pin |
| --- | --- |
| `actions/checkout` | v7 |
| `actions/setup-java` | v6 |
| `actions/setup-node` | v7 |
| `actions/setup-python` | v7 |
| `actions/cache` | v6 |
| `actions/upload-artifact` | v7 |
| `actions/download-artifact` | v8 |
| `actions/github-script` | v9 |
| `android-actions/setup-android` | v4 |
| `aquasecurity/trivy-action` | v0.36.0 |
| `github/codeql-action` (`init`, `analyze`, `upload-sarif`) | v4 |

Do not pin `trivy-action@master`. Do not SHA-pin like Haystack. JDK 17, `compileSdk` 35, and the job graph stay as ADR 0002 / OpenSpec.

The SPDD Norms list and `specification/pipelines/mobile-ci.md` GitHub Actions table SHALL list this same set. When a pin changes, update YAML, SPDD, the spec table, and this ADR together.

## Consequences

- Operators copy the six workflow files as-is; no extra SHA comments to keep in sync.
- A major-tag move (for example `setup-java@v7`) is a deliberate change: update this ADR and the spec table, then the YAML.
- `github-script@v9` forbids `require('@actions/github')` in scripts. The Checks-tab PDF step uses `github.rest.checks.create` only.
