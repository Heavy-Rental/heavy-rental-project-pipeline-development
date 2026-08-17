# Heavy Rental haystack-fast-api — GitHub Actions CI

Workflows and specifications for [Heavy-Rental/haystack-fast-api](https://github.com/Heavy-Rental/haystack-fast-api).

This tree (`haystack-fast-api-pipeline/`) authors Fast Feedback, Integration CI, Release packaging, and Academy **app CD** (`deploy-pipeline/`). It does not provision the VPC or ASGs (infra project). Copy workflows into [haystack-fast-api](https://github.com/Heavy-Rental/haystack-fast-api) like Release.

Start here: [`specification/README.md`](specification/README.md). App-repo CD checklist: [`docs/PREPARE-HAYSTACK-REPO.md`](docs/PREPARE-HAYSTACK-REPO.md).

| Path | Contents |
| --- | --- |
| `specification/` | Human index and pipeline walkthrough |
| `openspec/` | OpenSpec behavior (requirements + scenarios) |
| `spdd/` | OpenSPDD analysis + REASONS Canvas |
| `docs/` | Academy CD operate + [`PREPARE-HAYSTACK-REPO.md`](docs/PREPARE-HAYSTACK-REPO.md) |
| `fast-feedback-ci-pipeline/` | Integration-only feature-branch pipeline |
| `integration-pipeline/` | PR / `develop` merge gate |
| `release-pipeline/` | `develop` → `master` / GitHub Release + `uv build` + Docker/GHCR |
| `deploy-pipeline/` | Academy app CD (discover + compose; copy into the app repo) |
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
| Deploy the packaged service | Academy CD in `deploy-pipeline/` (copy into the app repo). Needs a public GHCR/ECR tag from Release |
| Operate the live system | Infra estate + this CD. See [`docs/BOOTSTRAP.md`](docs/BOOTSTRAP.md) |

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
