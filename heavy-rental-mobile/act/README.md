# Local `act` testing

This pipeline-development repo already installs [nektos/act](https://github.com/nektos/act) and Docker-outside-of-Docker in the devcontainer. You can smoke-test the mobile workflows here. You cannot faithfully run the full Android Gradle / CodeQL jobs from this repository.

## What works

| Command | What it proves |
| --- | --- |
| `./heavy-rental-mobile/act/run-act.sh list` | Callers resolve the reusable files |
| `./heavy-rental-mobile/act/run-act.sh smoke` | Assert caller runs under act (`ACT=true`) |
| `./heavy-rental-mobile/act/run-act.sh ci-smoke` | Same for the Integration CI reusable file |
| `./heavy-rental-mobile/act/run-act.sh dryrun` | Integration job graph (no containers) |
| `./heavy-rental-mobile/act/run-act.sh integration` | Same, with remote `Heavy-Rental/heavy-rental-mobile@develop` inputs |

Discovery mirrors (same pattern as REST API / portal) so `act -l` lists the reusable pipelines:

- `.github/workflows/mobile-fast-feedback.yml`
- `.github/workflows/mobile-ci.yml`
- `.github/workflows/mobile-release.yml`

Those mirrors are `workflow_call` only. Use `run-act.sh`, which stages the install filenames, runs act, then deletes the staged copies.

**Caller gate and act:** GitHub sets `github.workflow_ref` to the caller file. act leaves it empty, so the filename gate would always fail. The reusable workflows skip that check only when `ACT=true` (set by act, never set on GitHub-hosted runners). The reject path is only proven on GitHub.

## What does not work well in act

- **Integration from this repo without remote inputs** — checkout mode is `caller`, and this repo is not the Android app (`gradlew` is missing).
- **Full `:app:preBuild` / lint / test / assemble** — needs the Android SDK, a large image, and many minutes. Prefer running act **inside a clone of** `Heavy-Rental/heavy-rental-mobile` after copying the six YAML files.
- **CodeQL** — not supported by act.
- **Release caller** — no `workflow_dispatch`; it only fires on a published release or a `develop` → `master` PR. Use `list` to see the graph; do not expect `act push` to start it.

## Run from the application repo (full Integration)

```bash
git clone https://github.com/Heavy-Rental/heavy-rental-mobile.git
cd heavy-rental-mobile
mkdir -p .github/workflows
# copy the six files from this pipeline-development tree, then:
act workflow_dispatch -W .github/workflows/mobile-fast-feedback-caller.yml
```

No secrets are required for v1.
