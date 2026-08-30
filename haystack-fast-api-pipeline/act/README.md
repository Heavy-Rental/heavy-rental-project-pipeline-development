# Local `act` testing

This pipeline-development repo already installs [nektos/act](https://github.com/nektos/act) and Docker-outside-of-Docker in the devcontainer. You can smoke-test the haystack workflows here. You cannot faithfully run full `uv sync` / pytest / CodeQL jobs from this repository (this tree is not the FastAPI app).

## What works

| Command | What it proves |
| --- | --- |
| `./haystack-fast-api-pipeline/act/run-act.sh list` | Callers resolve the reusable files |
| `./haystack-fast-api-pipeline/act/run-act.sh smoke` | Fast Feedback Assert caller runs under act (`ACT=true`) |
| `./haystack-fast-api-pipeline/act/run-act.sh ci-smoke` | Same for the Integration CI reusable file |
| `./haystack-fast-api-pipeline/act/run-act.sh dryrun` | Fast Feedback Integration job graph (no containers) |
| `./haystack-fast-api-pipeline/act/run-act.sh integration` | Same Fast Feedback Integration dry-run, with remote `Heavy-Rental/haystack-fast-api@develop` inputs |

`run-act.sh` stages the install filenames, runs act, then deletes the staged copies.

**Caller gate and act:** GitHub sets `github.workflow_ref` to the caller file. act leaves it empty, so the filename gate would always fail. The reusable workflows skip that check only when `ACT=true` (set by act, never set on GitHub-hosted runners). The reject path is only proven on GitHub.

## What does not work well in act

- **Integration from this repo without remote inputs** — checkout mode is `caller`, and this repo is not the Haystack app (`uv.lock` is missing).
- **Full `uv sync` / Ruff / pytest** — the Haystack/ML lock is large. Prefer running act **inside a clone of** `Heavy-Rental/haystack-fast-api` after copying the six GitHub Flow YAML files.
- **CodeQL** — not supported by act.
- **Release caller** — `workflow_dispatch` only (it does **not** fire on a published GitHub Release or a `develop` → `master` PR; Publish *creates* the GitHub Release). The run checks out `master` and is heavy (uv, Docker, DAST). Prefer running it **inside a clone of** `Heavy-Rental/haystack-fast-api`.

## Run from the application repo (full Integration)

```bash
git clone https://github.com/Heavy-Rental/haystack-fast-api.git
cd haystack-fast-api
mkdir -p .github/workflows
# copy the six GitHub Flow YAML files from this pipeline-development tree, then:
act workflow_dispatch -W .github/workflows/haystack-fast-feedback-caller.yml
```
