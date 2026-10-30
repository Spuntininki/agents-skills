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
git worktree list --porcelain | grep '^worktree ' | awk '{print $2}' | while read -r wt_path; do
  if [[ "$wt_path" =~ \.worktrees/issue-([0-9]+) ]]; then
    issue_num="${BASH_REMATCH[1]}"
    echo "Checking status for issue #$issue_num ($wt_path)..."

    # Query GitHub CLI for associated PR state
    pr_state=$(gh pr list --head "feat/issue-$issue_num-" --state all --json state -q '.[0].state' 2>/dev/null || echo "")
    if [ -z "$pr_state" ]; then
      pr_state=$(gh pr list --head "fix/issue-$issue_num-" --state all --json state -q '.[0].state' 2>/dev/null || echo "")
    fi

    if [ "$pr_state" == "MERGED" ]; then
      echo "✅ PR for issue #$issue_num is MERGED. Cleaning up..."
      
      # Remove worktree
      git worktree remove "$wt_path" --force || rm -rf "$wt_path"
      
      # Delete associated local branch
      branch_name=$(git branch --list "*issue-$issue_num-*" | tr -d ' *' | head -n 1 || true)
      if [ -n "$branch_name" ]; then
        echo "Deleting local branch: $branch_name"
        git branch -D "$branch_name" 2>/dev/null || true
      fi
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
echo "===> Cleanup complete."
