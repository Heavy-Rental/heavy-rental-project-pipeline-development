# Heavy Rental haystack-fast-api — GitHub Actions CI

Workflows and specifications for [Heavy-Rental/haystack-fast-api](https://github.com/Heavy-Rental/haystack-fast-api).

This tree (`haystack-fast-api-pipeline/`) authors the **CI family only**: Fast Feedback, Integration CI, and Release packaging. It does not provision infrastructure, deploy the service, or operate production. Those concerns belong to another project.

Start here: [`specification/README.md`](specification/README.md).

| Path | Contents |
| --- | --- |
| `specification/` | Human index and pipeline walkthrough |
| `openspec/` | OpenSpec behavior (requirements + scenarios) |
| `spdd/` | OpenSPDD analysis + REASONS Canvas |
| `fast-feedback-ci-pipeline/` | Integration-only feature-branch pipeline |
| `integration-pipeline/` | PR / `develop` merge gate |
| `release-pipeline/` | `develop` → `master` / GitHub Release + `uv build` + Docker/GHCR |
| `act/` | Local `act` smoke tests (see [`act/README.md`](act/README.md)) |

## GitHub Flow

```
feature branch push  →  Fast Feedback (Integration only)
PR / push → develop  →  Integration CI (full gates, no packaging)
develop → master PR or published GitHub Release
                     →  Release (full gates + uv build + Docker image)
```

Release stops at **packaged artifacts** (wheel, sdist, image tar; GHCR push off pull request). A later project consumes those artifacts to deploy.

## Pipeline boundaries

| Concern | This family |
| --- | --- |
| Build, test, and package | In scope |
| Create or change infrastructure | Out of scope (another project) |
| Deploy the packaged service | Out of scope (another project; consumes Release artifacts) |
| Operate the live system | Out of scope (another project; after go-live) |

Operate needs knowledge of the running platform. It does not create that platform, and this CI family does not either.

## Toolchain

**Python 3.12 + uv + Ruff + pytest + Haystack**, not Java / Gradle / Node.

| Concern | Tool |
| --- | --- |
| Interpreter | CPython 3.12 |
| Lock + install | uv (`uv.lock`) |
| Integration smoke | `haystack.Pipeline`, `create_app`, indexing + intake builders |
| Lint | Ruff |
| Tests | pytest |
| SAST / SCA | Semgrep `p/python`, pip-audit (report), Trivy |
| Code scanning | CodeQL `python` |
| Package | `uv build` + Docker image (tar; GHCR off PR) |
