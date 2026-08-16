#!/usr/bin/env bash
# Stage mobile caller + reusable workflows into .github/workflows/ (install names)
# and run nektos/act. Discovery mirrors (mobile-*.yml) stay committed; staged
# caller/install names are removed on exit so this repo does not grow push/PR
# triggers that would try to build Android from pipeline-development.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WF="${ROOT}/.github/workflows"
MOBILE="${ROOT}/heavy-rental-mobile"
EVENTS="${MOBILE}/act/events"
STAGED_FILES=(
  "${WF}/mobile-fast-feedback-caller.yml"
  "${WF}/fast-feedback-pipeline.yml"
  "${WF}/mobile-ci-caller.yml"
  "${WF}/integration-pipeline.yml"
  "${WF}/mobile-release-caller.yml"
  "${WF}/release-pipeline.yml"
)

cleanup() {
  rm -f "${STAGED_FILES[@]}"
}
trap cleanup EXIT

stage() {
  mkdir -p "${WF}"
  cp "${MOBILE}/fast-feedback-ci-pipeline/mobile-fast-feedback-caller.yml" "${WF}/mobile-fast-feedback-caller.yml"
  cp "${MOBILE}/fast-feedback-ci-pipeline/fast-feedback-pipeline.yml" "${WF}/fast-feedback-pipeline.yml"
  cp "${MOBILE}/integration-pipeline/mobile-ci-caller.yml" "${WF}/mobile-ci-caller.yml"
  cp "${MOBILE}/integration-pipeline/integration-pipeline.yml" "${WF}/integration-pipeline.yml"
  cp "${MOBILE}/release-pipeline/mobile-release-caller.yml" "${WF}/mobile-release-caller.yml"
  cp "${MOBILE}/release-pipeline/release-pipeline.yml" "${WF}/release-pipeline.yml"
}

usage() {
  cat <<'EOF'
Usage: heavy-rental-mobile/act/run-act.sh <command>

  list       List staged mobile callers (act -l)
  smoke      Run Fast Feedback Assert caller in act (ACT=true skips empty workflow_ref)
  dryrun     Dry-run Fast Feedback Integration (no containers; may clone actions)
  integration
             Dry-run Fast Feedback Integration with remote checkout of
             Heavy-Rental/heavy-rental-mobile@develop
  ci-smoke   Run Integration CI Assert caller in act
  help       This message

Requires: act (devcontainer feature), Docker socket.
Full Gradle / Android SDK / CodeQL jobs are not recommended in act from
this repo — use smoke/dryrun, or copy the workflows into the mobile app
repo and run act there.
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
    act -l -W "${WF}/mobile-fast-feedback-caller.yml"
    act -l -W "${WF}/mobile-ci-caller.yml"
    act -l -W "${WF}/mobile-release-caller.yml"
    ;;
  smoke)
    # act cannot select a nested reusable job from the caller file (-j assert-caller
    # is invisible). Present the reusable workflow under the allowed caller filename
    # so github.workflow_ref matches the gate, then run only Assert caller.
    echo "==> Live Assert caller (reusable presented as allowed caller filename)"
    cp "${WF}/fast-feedback-pipeline.yml" "${WF}/mobile-fast-feedback-caller.yml"
    act workflow_call \
      "${ACT_COMMON[@]}" \
      -W "${WF}/mobile-fast-feedback-caller.yml" \
      -j assert-caller
    ;;
  dryrun)
    act workflow_dispatch \
      "${ACT_COMMON[@]}" \
      -W "${WF}/mobile-fast-feedback-caller.yml" \
      -j integration \
      -n \
      -e "${EVENTS}/workflow_dispatch.json"
    ;;
  integration)
    act workflow_dispatch \
      "${ACT_COMMON[@]}" \
      -W "${WF}/mobile-fast-feedback-caller.yml" \
      -j integration \
      -n \
      -e "${EVENTS}/workflow_dispatch-remote.json"
    ;;
  ci-smoke)
    echo "==> Live Assert caller for Integration CI"
    cp "${WF}/integration-pipeline.yml" "${WF}/mobile-ci-caller.yml"
    act workflow_call \
      "${ACT_COMMON[@]}" \
      -W "${WF}/mobile-ci-caller.yml" \
      -j assert-caller
    ;;
  *)
    usage
    exit 1
    ;;
esac
