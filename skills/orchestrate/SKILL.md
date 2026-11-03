---
name: orchestrate
description: >-
  Supervises and executes multi-issue epics using isolated git worktrees,
  concurrent subagents for parallel slices, an Epic Integration Branch,
  and deterministic cleanup.
---

# /orchestrate

Supervise and execute multi-issue epics end-to-end against an **Epic Integration Branch** (`epic/issue-<epic>-<slug>`).

## Workflow

1. **Init Epic Branch & Milestone**:
   - Fetch parent issue and milestone:
     ```bash
     gh issue view <epic-number> --json title,body,milestone
     MILESTONE=$(gh issue view <epic-number> --json milestone -q .milestone.title 2>/dev/null || echo "")
     ```
   - Ensure integration branch `epic/issue-<epic-number>-<slug>` exists on remote (branched from `origin/main`), then fetch it locally.

2. **Identify Unblocked Slices**:
   - Parse parent Epic checklist (`- [ ]`). Slices whose dependencies are all `[x]` (or `None`) are unblocked.
   - If multiple unblocked slices are marked `Parallel ⚡`, provision and dispatch them **concurrently**.
   - If unblocked slice is `Serial 🔒`, dispatch exclusively.

3. **Provision Worktree & Dispatch**:
   - For each unblocked slice `#<id>`:
     ```bash
     git fetch origin epic/issue-<epic-number>-<slug>
     git worktree add .worktrees/issue-<id> -b feat/issue-<id>-<slug> origin/epic/issue-<epic-number>-<slug>
     ```
   - Dispatch executor subagent into `.worktrees/issue-<id>`:
     > "Implement issue `#<id>` using `/implement <id>`. You are in an isolated worktree on the feature branch. Submit PR targeting: `gh pr create --base epic/issue-<epic-number>-<slug> ${MILESTONE:+-m \"$MILESTONE\"}`."

4. **Review, Sync & Merge (Asynchronous Loop)**:
   - When an executor opens a PR: verify locally in `.worktrees/issue-<id>` (`make test`, `make lint`, diff review).
   - If fixes are needed, message the executor in that worktree for atomic revisions.
   - Once approved, merge into the epic branch:
     ```bash
     gh pr merge <pr-number> --squash --delete-branch
     ```
   - **Sync Active Sibling Worktrees**: If other parallel worktrees are active, rebase them against the updated epic branch:
     ```bash
     git -C .worktrees/issue-<sibling-id> fetch origin epic/issue-<epic-number>-<slug>
     git -C .worktrees/issue-<sibling-id> rebase origin/epic/issue-<epic-number>-<slug>
     ```

5. **Cleanup & Advance**:
   - Remove finished worktree: `git worktree remove .worktrees/issue-<id> --force && git branch -D feat/issue-<id>-<slug> 2>/dev/null || true` (or run `<skill-dir>/scripts/cleanup-worktrees.sh` to batch-prune all merged worktrees without reading its source).
   - Update parent Epic checklist: mark completed slice `- [x] ... #<id>`.
   - If pending slices remain, return to **Step 2**.

6. **Release Gate**:
   - When all slices are `[x]`, open final release PR:
     ```bash
     gh pr create --base main --head epic/issue-<epic-number>-<slug> ${MILESTONE:+-m "$MILESTONE"} --title "feat: <epic-title>" --body "Closes #<epic-number>"
     ```
   - Once merged into `main`, CD triggers once for atomic deployment. Close Epic, delete remote epic branch, and close Milestone if complete:
     ```bash
     if [ -n "$MILESTONE" ]; then
       gh api repos/:owner/:repo/milestones/$(gh api repos/:owner/:repo/milestones -q ".[] | select(.title==\"$MILESTONE\") | .number") -X PATCH -f state=closed 2>/dev/null || true
     fi
     ```
