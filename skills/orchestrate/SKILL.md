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

1. **Init Epic Branch, Milestone & Living Dashboard**:
   - Fetch parent issue and milestone:
     ```bash
     gh issue view <epic-number> --json title,body,milestone
     MILESTONE=$(gh issue view <epic-number> --json milestone -q .milestone.title 2>/dev/null || echo "")
     ```
   - Ensure integration branch `epic/issue-<epic-number>-<slug>` exists on remote (branched from `origin/main`), then fetch it locally.
   - **Initialize Living Dashboard Comment** on parent Epic issue:
     Post (or locate) a dedicated tracking comment with a Markdown status table. This comment will be updated live as slice PRs are created, revised, and merged:
     ```bash
     DASHBOARD_ID=$(gh api repos/:owner/:repo/issues/<epic-number>/comments \
       --jq '.[] | select(.body | contains("## 📊 Epic Orchestration Dashboard")) | .id' | head -n 1)

     if [ -z "$DASHBOARD_ID" ]; then
       DASHBOARD_ID=$(gh issue comment <epic-number> --body "$(cat << 'EOF'
     ## 📊 Epic Orchestration Dashboard

     | Slice Issue | Mode | PR | Status | Branch |
     | :--- | :--- | :--- | :--- | :--- |
     | Initializing... | — | — | ⏳ Planning | — |

     - **Integration Branch**: `epic/issue-<epic-number>-<slug>`
     - **Milestone**: `${MILESTONE:-None}`
     EOF
     )" | grep -oE '[0-9]+$')
     fi
     ```

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
   - When an executor opens a PR:
     - Update the Dashboard comment row for `#<id>` to `👀 Ready for Review` with the PR link.
     - Verify locally in `.worktrees/issue-<id>` (`make test`, `make lint`, diff review).
   - **Human-in-the-Loop Checkpoint**:
     - Notify developer with PR link and review summary:
       > "PR #<pr-number> ready for slice #<id>. Review in GitHub or run `/revise <pr-number>` if changes are desired."
     - If adjustments are requested, update row to `🛠️ Revising` and dispatch a **Revise Subagent** targeting the original issue/PR inside `.worktrees/issue-<id>`:
       > "Apply review feedback to PR #<pr-number> (Issue #<id>) using `/revise <pr-number> "<feedback>"`. Operate directly in `.worktrees/issue-<id>`, apply corrections across domain logic and tests, commit to the original PR branch, and report back."
     - The subagent pushes directly to the existing PR branch (no new issues created), preserving the Epic checklist and milestone counters.
   - Once approved (by developer or automated check), merge into the epic branch:
     ```bash
     gh pr merge <pr-number> --squash --delete-branch
     ```
   - **Update Dashboard Table**: Patch comment row for `#<id>` to `🚀 MERGED`:
     ```bash
     gh api repos/:owner/:repo/issues/comments/$DASHBOARD_ID -X PATCH -f body="<updated-table>"
     ```
   - **Sync Active Sibling Worktrees**: If other parallel worktrees are active, rebase them against the updated epic branch:
     ```bash
     git -C .worktrees/issue-<sibling-id> fetch origin epic/issue-<epic-number>-<slug>
     git -C .worktrees/issue-<sibling-id> rebase origin/epic/issue-<epic-number>-<slug>
     ```
     - **Rebase Conflict Protocol**:
       - *Trivial Conflicts (adjacent imports, route lists, dependency manifests)*: Resolve inline by preserving both additions, run `git -C .worktrees/issue-<sibling-id> add <file>`, and execute `git -C .worktrees/issue-<sibling-id> rebase --continue`.
       - *Semantic / Architectural Conflicts*: Abort the rebase (`git -C .worktrees/issue-<sibling-id> rebase --abort`) and message the sibling executor subagent to adapt its implementation to the updated Epic branch before proceeding.

5. **Cleanup & Advance**:
   - Run the automated cleanup script:
     ```bash
     bash <skill-dir>/scripts/cleanup-worktrees.sh
     ```
     > **Note**: Do NOT inspect `cleanup-worktrees.sh` source code. It is a pre-packaged utility that safely verifies PR merge state, tears down Compose containers/volumes, removes finished worktrees, and prunes dangling Docker images.
   - Update parent Epic checklist: mark completed slice `- [x] ... #<id>`.
   - If pending slices remain, return to **Step 2**.

6. **Release Gate**:
   - When all slices are `[x]`, open final release PR:
     ```bash
     gh pr create --base main --head epic/issue-<epic-number>-<slug> ${MILESTONE:+-m "$MILESTONE"} --title "feat: <epic-title>" --body "Closes #<epic-number>"
     ```
   - Update Dashboard comment marking all slices as `🚀 MERGED` and linking the final Release PR.
   - Once merged into `main`, CD triggers once for atomic deployment. Run final cleanup, close Epic, delete remote epic branch, and close Milestone if complete:
     ```bash
     bash <skill-dir>/scripts/cleanup-worktrees.sh

     if [ -n "$MILESTONE" ]; then
       gh api repos/:owner/:repo/milestones/$(gh api repos/:owner/:repo/milestones -q ".[] | select(.title==\"$MILESTONE\") | .number") -X PATCH -f state=closed 2>/dev/null || true
     fi
     ```
