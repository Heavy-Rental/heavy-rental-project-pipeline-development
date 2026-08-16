#!/usr/bin/env bash
# Stage haystack caller + reusable workflows into .github/workflows/ (install names)
# and run nektos/act. Staged caller/install names are removed on exit so this
# repo does not grow push/PR triggers that would try to build Haystack from
# pipeline-development.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WF="${ROOT}/.github/workflows"
HAYSTACK="${ROOT}/haystack-fast-api-pipeline"
EVENTS="${HAYSTACK}/act/events"
STAGED_FILES=(
  "${WF}/haystack-fast-feedback-caller.yml"
  "${WF}/fast-feedback-pipeline.yml"
  "${WF}/haystack-ci-caller.yml"
  "${WF}/integration-pipeline.yml"
  "${WF}/haystack-release-caller.yml"
  "${WF}/release-pipeline.yml"
)

cleanup() {
  rm -f "${STAGED_FILES[@]}"
}
trap cleanup EXIT

stage() {
  mkdir -p "${WF}"
  cp "${HAYSTACK}/fast-feedback-ci-pipeline/haystack-fast-feedback-caller.yml" "${WF}/haystack-fast-feedback-caller.yml"
  cp "${HAYSTACK}/fast-feedback-ci-pipeline/fast-feedback-pipeline.yml" "${WF}/fast-feedback-pipeline.yml"
  cp "${HAYSTACK}/integration-pipeline/haystack-ci-caller.yml" "${WF}/haystack-ci-caller.yml"
  cp "${HAYSTACK}/integration-pipeline/integration-pipeline.yml" "${WF}/integration-pipeline.yml"
  cp "${HAYSTACK}/release-pipeline/haystack-release-caller.yml" "${WF}/haystack-release-caller.yml"
  cp "${HAYSTACK}/release-pipeline/release-pipeline.yml" "${WF}/release-pipeline.yml"
}

usage() {
  cat <<'EOF'
Usage: haystack-fast-api-pipeline/act/run-act.sh <command>

  list       List staged haystack callers (act -l)
  smoke      Run Fast Feedback Assert caller in act (ACT=true skips empty workflow_ref)
  dryrun     Dry-run Fast Feedback Integration (no containers; may clone actions)
  integration
             Dry-run Fast Feedback Integration with remote checkout of
             Heavy-Rental/haystack-fast-api@develop
  ci-smoke   Run Integration CI Assert caller in act
  help       This message

Requires: act (devcontainer feature), Docker socket.
Full uv sync / pytest / CodeQL jobs are not recommended in act from
this repo — use smoke/dryrun, or copy the workflows into the
haystack-fast-api app repo and run act there.
EOF
}

cd "${ROOT}"
command -v act >/dev/null || { echo "act is not on PATH" >&2; exit 1; }

CMD="${1:-help}"
case "${CMD}" in
  help|-h|--help)
    usage
    exit 0
    ;;
esac

stage

# Pin the already-pulled act image so the first-run picker never blocks CI/scripts.
ACT_COMMON=(
  -P ubuntu-latest=catthehacker/ubuntu:act-latest
  --pull=false
)

case "${CMD}" in
  list)
    act -l -W "${WF}/haystack-fast-feedback-caller.yml"
    act -l -W "${WF}/haystack-ci-caller.yml"
    act -l -W "${WF}/haystack-release-caller.yml"
    ;;
  smoke)
    echo "==> Live Assert caller (reusable presented as allowed caller filename)"
    cp "${WF}/fast-feedback-pipeline.yml" "${WF}/haystack-fast-feedback-caller.yml"
    act workflow_call \
      "${ACT_COMMON[@]}" \
      -W "${WF}/haystack-fast-feedback-caller.yml" \
      -j assert-caller
    ;;
  dryrun)
    act workflow_dispatch \
      "${ACT_COMMON[@]}" \
      -W "${WF}/haystack-fast-feedback-caller.yml" \
      -j integration \
      -n \
      -e "${EVENTS}/workflow_dispatch.json"
    ;;
  integration)
    act workflow_dispatch \
      "${ACT_COMMON[@]}" \
      -W "${WF}/haystack-fast-feedback-caller.yml" \
      -j integration \
      -n \
      -e "${EVENTS}/workflow_dispatch-remote.json"
    ;;
  ci-smoke)
    echo "==> Live Assert caller for Integration CI"
    cp "${WF}/integration-pipeline.yml" "${WF}/haystack-ci-caller.yml"
    act workflow_call \
      "${ACT_COMMON[@]}" \
      -W "${WF}/haystack-ci-caller.yml" \
      -j assert-caller
    ;;
  *)
    usage
    exit 1
    ;;
esac
