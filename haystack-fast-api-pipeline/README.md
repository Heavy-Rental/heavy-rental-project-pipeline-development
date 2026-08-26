# Heavy Rental haystack-fast-api — GitHub Actions CI

Workflows and specifications for [Heavy-Rental/haystack-fast-api](https://github.com/Heavy-Rental/haystack-fast-api).

This tree (`haystack-fast-api-pipeline/`) authors Fast Feedback, Integration CI, Release packaging, and **Academy + paid app CD** (`deploy-pipeline/`). It does not provision the VPC or ASGs (infra project). Copy workflows into [haystack-fast-api](https://github.com/Heavy-Rental/haystack-fast-api) like Release.

Start here: [`specification/README.md`](specification/README.md). App-repo CD checklist: [`docs/PREPARE-HAYSTACK-REPO.md`](docs/PREPARE-HAYSTACK-REPO.md).

| Path | Contents |
| --- | --- |
| `specification/` | Human index and CI + CD walkthroughs |
| `openspec/` | OpenSpec behavior (requirements + scenarios) |
| `spdd/` | OpenSPDD analysis + REASONS Canvas |
| `docs/adr/` | ADRs 0001–0010 (CI 0005–0008; CD 0001–0004, 0010 two Actions; 0009 spans both) |
| `docs/` | App CD operate ([`BOOTSTRAP.md`](docs/BOOTSTRAP.md), [`PREPARE-HAYSTACK-REPO.md`](docs/PREPARE-HAYSTACK-REPO.md), [`samples/.env.prod`](docs/samples/.env.prod)) |
| `fast-feedback-ci-pipeline/` | Integration-only feature-branch pipeline |
| `integration-pipeline/` | PR / `develop` merge gate |
| `release-pipeline/` | Manual `workflow_dispatch` on `master`: QC + image + DAST + public GHCR + GitHub Release |
| `deploy-pipeline/` | Academy + paid app CD (discover + compose; copy into the app repo) |
| `act/` | Local `act` smoke tests (see [`act/README.md`](act/README.md)) |

## GitHub Flow

```
feature branch push  →  Fast Feedback (Integration only; sole Integration-stage run for that SHA)
PR / push → develop  →  Integration CI (Integration reuses Fast Feedback on PR; full gates; SAST here)
workflow_dispatch     →  Release (master + QC + image + DAST + public GHCR + GitHub Release)
```

Release stops at **packaged artifacts** (wheel, sdist, image tar, public GHCR, GitHub Release). It does not deploy. Academy and paid CD in `deploy-pipeline/` consume a public GHCR/ECR tag or the tar. SAST and CodeQL stay on Integration CI.

## Pipeline boundaries

| Concern | This family |
| --- | --- |
| Build, test, and package | In scope |
| Create or change infrastructure | Out of scope (another project) |
| Deploy the packaged service | Academy and paid CD in `deploy-pipeline/` (copy into the app repo). Needs a public GHCR/ECR tag from Release |
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
| Package | `uv build` + Docker image tar; Publish pushes GHCR + GitHub Release |
