#!/usr/bin/env bash
# =============================================================================
# cleanup-worktrees.sh
# -----------------------------------------------------------------------------
# Deterministically cleans up finished worktrees and local branches.
#
# Scans `.worktrees/issue-<number>`:
# 1. Inspects the GitHub PR state for issue-<number>.
# 2. If the PR is MERGED, safely removes the worktree and deletes the local branch.
# 3. Prunes git worktree metadata.
# =============================================================================

set -euo pipefail

WORKTREE_DIR=".worktrees"

if [ ! -d "$WORKTREE_DIR" ]; then
  echo "No $WORKTREE_DIR directory found in current repository."
  exit 0
fi

echo "===> Scanning $WORKTREE_DIR for completed worktrees..."

# Enumerate active worktrees under .worktrees/issue-*
git worktree list --porcelain | grep '^worktree ' | sed 's/^worktree //' | while IFS= read -r wt_path; do
  if [[ "$wt_path" =~ \.worktrees/issue-([0-9]+) ]]; then
    issue_num="${BASH_REMATCH[1]}"
    echo "Checking status for issue #$issue_num ($wt_path)..."

    # Query GitHub CLI for associated PR state across common branch conventions
    pr_state=""
    for prefix in feat fix chore refactor docs codex ""; do
      head_query="${prefix:+${prefix}/}issue-$issue_num-"
      pr_state=$(gh pr list --head "$head_query" --state all --json state -q '.[0].state' 2>/dev/null || echo "")
      if [ -n "$pr_state" ]; then
        break
      fi
    done

    if [ "$pr_state" == "MERGED" ]; then
      echo "✅ PR for issue #$issue_num is MERGED. Cleaning up..."

      # Teardown Docker Compose containers, networks, and volumes if present in worktree
      if command -v docker &>/dev/null; then
        for compose_file in "$wt_path/docker-compose.yml" "$wt_path/docker-compose.yaml" "$wt_path/compose.yaml" "$wt_path/compose.yml"; do
          if [ -f "$compose_file" ]; then
            echo "Tearing down Docker Compose containers and volumes for issue #$issue_num..."
            docker compose --project-directory "$wt_path" -f "$compose_file" down -v --remove-orphans 2>/dev/null || true
            break
          fi
        done
      fi

      # Remove worktree
      git worktree remove "$wt_path" --force || rm -rf "$wt_path"
      
      # Delete associated local branches
      git branch --list "*issue-$issue_num-*" | tr -d ' *' | while IFS= read -r branch_name; do
        if [ -n "$branch_name" ]; then
          echo "Deleting local branch: $branch_name"
          git branch -D "$branch_name" 2>/dev/null || true
        fi
      done
    elif [ "$pr_state" == "OPEN" ]; then
      echo "⏳ PR for issue #$issue_num is still OPEN. Keeping worktree."
    elif [ -z "$pr_state" ]; then
      echo "⚠️ No PR found for issue #$issue_num. Keeping worktree for safety."
    else
      echo "ℹ️ Issue #$issue_num state is '$pr_state'."
    fi
  fi
done

# Prune git internal metadata
git worktree prune

# Prune dangling docker images
if command -v docker &>/dev/null; then
  echo "Pruning dangling docker images..."
  docker image prune -f 2>/dev/null || true
fi

echo "===> Cleanup complete."
