#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# setup-labels.sh
# Configures standard structured labels in a GitHub repository using gh CLI.
# Safe to re-run: uses --force to create or update existing labels idempotently.
#
# Usage:
#   ./scripts/setup-labels.sh
#   ./scripts/setup-labels.sh -R owner/repo
# -----------------------------------------------------------------------------

set -euo pipefail

REPO_ARG=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    -R|--repo)
      REPO_ARG="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: $0 [-R owner/repo]"
      exit 0
      ;;
    *)
      REPO_ARG="$1"
      shift
      ;;
  esac
done

if ! command -v gh >/dev/null 2>&1; then
  echo "Error: GitHub CLI (gh) is not installed." >&2
  exit 1
fi

GH_FLAGS=()
if [ -n "$REPO_ARG" ]; then
  GH_FLAGS+=("-R" "$REPO_ARG")
  echo "===> Setting up standard labels for repository: $REPO_ARG"
else
  echo "===> Setting up standard labels for current repository"
fi

# Format: name|color|description
LABELS=(
  "needs:preview|ff9800|Requires developer local build and visual verification before PR"
  "area:frontend|0075ca|Frontend UI components, styling, client-side logic"
  "area:backend|0052cc|Backend APIs, database models, server-side services"
  "area:infra|5319e7|CI/CD, Docker, build tooling, deployment infrastructure"
  "type:feat|a2eeef|New feature or cohesive capability"
  "type:bug|d73a4a|Bug fix or unexpected failure"
  "type:refactor|cfd3d7|Code refactoring without behavioral change"
  "type:epic|3e4b9e|Parent epic coordinating multi-issue decomposition"
  "type:chore|e4e669|Maintenance, tooling, or dependency updates"
  "exec:parallel|1d76db|Independent slice safe for concurrent worktree execution"
  "exec:serial|fbca04|Dependent slice requiring sequential execution"
)

for item in "${LABELS[@]}"; do
  IFS="|" read -r name color desc <<< "$item"
  echo "  • Configuring label: $name (#$color)"
  gh label create "$name" --color "$color" --description "$desc" --force "${GH_FLAGS[@]}" >/dev/null
done

echo ""
echo "✅ All standard labels configured successfully!"
