# Heavy Rental mobile — GitHub Actions CI

Workflows and specifications for [Heavy-Rental/heavy-rental-mobile](https://github.com/Heavy-Rental/heavy-rental-mobile).

This tree authors Fast Feedback, Integration CI, and unsigned Release APK packaging. There is **no Academy app CD**.

Start here: [`specification/README.md`](specification/README.md).

| Path | Contents |
| --- | --- |
| `specification/` | Human index and CI walkthrough |
| `openspec/` | OpenSpec behavior (requirements + scenarios) |
| `spdd/` | OpenSPDD analysis + REASONS Canvas |
| `docs/adr/` | ADRs for the CI family |
| `fast-feedback-ci-pipeline/` | Integration-only feature-branch pipeline |
| `integration-pipeline/` | PR / `develop` merge gate |
| `release-pipeline/` | `develop` → `master` / GitHub Release + unsigned APK |
| `act/` | Local `act` smoke tests (see [`act/README.md`](act/README.md)) |
