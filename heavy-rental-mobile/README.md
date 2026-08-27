# Heavy Rental mobile — GitHub Actions CI

Workflows and specifications for [Heavy-Rental/heavy-rental-mobile](https://github.com/Heavy-Rental/heavy-rental-mobile).

This tree authors Fast Feedback, Integration CI, unsigned Release APK packaging, MobSF DAST, and a GitHub Release. There is **no Academy app CD** and no GHCR image.

Start here: [`specification/README.md`](specification/README.md).

| Path | Contents |
| --- | --- |
| `specification/` | Human index and CI walkthrough |
| `openspec/` | OpenSpec behavior (requirements + scenarios) |
| `spdd/` | OpenSPDD analysis + REASONS Canvas |
| `docs/adr/` | ADRs 0001–0007 for the CI family |
| `fast-feedback-ci-pipeline/` | Integration-only feature-branch pipeline |
| `integration-pipeline/` | PR / `develop` merge gate |
| `release-pipeline/` | Manual `workflow_dispatch` on `master`: QC + unsigned APK + MobSF + GitHub Release |
| `act/` | Local `act` smoke tests (see [`act/README.md`](act/README.md)) |

## GitHub Flow

```
feature branch push  →  Fast Feedback (Integration only; sole Integration-stage run for that SHA)
PR / push → develop  →  Integration CI (Integration reuses Fast Feedback on PR; full gates; SAST here)
workflow_dispatch     →  Release (master + QC + APK + MobSF + GitHub Release)
```

Release stops at **packaged artifacts** (unsigned APK, MobSF reports, GitHub Release). It does not deploy. SAST, CodeQL, and Mock Contract Tests stay on Integration CI.

## Pipeline boundaries

| Concern | This family |
| --- | --- |
| Build, test, and package | In scope |
| Create or change infrastructure | Out of scope (another project) |
| Deploy the packaged app | Out of scope (no Academy mobile CD) |
| Operate the live system | Out of scope |
