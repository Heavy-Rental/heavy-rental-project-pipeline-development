# Architecture Decision Records (mobile CI)

Conflict order: **OpenSpec → OpenSPDD → ADR → YAML**.

This project has **no Academy CD**. All ADRs belong to `add-mobile-ci-pipeline`.

| ID | Title |
| --- | --- |
| [0001](0001-mobile-ci-reusable-caller.md) | Reusable workflows plus a sole-allowed caller |
| [0002](0002-mobile-ci-jdk17.md) | JDK 17, not 21 |
| [0003](0003-mobile-ci-unsigned-apk.md) | Release APK is unsigned; no GHCR |
| [0004](0004-mobile-ci-mocks-on-integration.md) | Mock contracts run on Integration CI only |
| [0005](0005-mobile-ci-action-majors.md) | Current stable GitHub Action majors (not SHA pins) |
| [0006](0006-mobile-ci-mockoon-only.md) | Mockoon-only; required scripts; no Prism |
| [0007](0007-mobile-ci-release-dispatch-dast.md) | Release is `workflow_dispatch` only; MobSF DAST + Publish; SAST stays on Integration CI |

Application ADR 003 (returnNotes echo, Mockoon-only) lives in `Heavy-Rental/heavy-rental-mobile`, not this table. Pipeline ADR 0003 is unsigned APK / no GHCR.
