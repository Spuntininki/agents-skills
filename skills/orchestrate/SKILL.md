---
name: orchestrate
description: >-
  Supervises and executes multi-issue epics using isolated git worktrees,
  managing dependencies, iterative feedback loops, and subagent executors.
---

# /orchestrate

Supervise, coordinate, and execute multi-issue epics end-to-end. Dispatches executor subagents into isolated git worktrees, manages dependency ordering, enforces iterative verification before merge, and guarantees deterministic workspace cleanup.

## Guiding Principles

- **Deterministic Worktree Isolation (`.worktrees/issue-<number>`)**:
  - Every child slice executes in its own dedicated git worktree located at `.worktrees/issue-<number>` on a branch named `feat/issue-<number>-<slug>` (or `fix/issue-<number>-<slug>`).
  - Completely isolates filesystem changes, test databases, node_modules, and git operations from the main workspace and other concurrent agents.
- **Iterative Feedback Loop (Anti-One-Shot SDD)**:
  - Real-world development is iterative, not one-shot. Any bug, edge case, regression, or visual/behavioral adjustment introduced during the slice's implementation MUST be fixed inside that slice's worktree before merging.
  - Never open new issues for bugs introduced within the current unmerged slice. Keep refining the slice until all tests pass and verification criteria are satisfied.
  - Only genuine scope creep (net-new requirements not in the slice's spec) should be deferred to a separate issue.
- **Deterministic Cleanup**:
  - Once a slice's PR is merged into `main`, its worktree and local branch are purged immediately (`git worktree remove` + `git branch -D` + `git worktree prune`).
  - Run `scripts/cleanup-worktrees.sh` to safely purge any lingering merged worktrees.
- **Tracking Issue as State Machine**:
  - The parent Epic checklist (`- [ ] 1. #<child> ...`) is the single source of truth for execution state.
  - As each child PR merges, the orchestrator checks off the item (`[x] 1. #<child>`), unblocking downstream slices.
- **Strict Role Separation**:
  - The orchestrator supervises the macro execution graph and state.
  - Executor subagents perform the actual implementation (`/implement`) inside their assigned worktree.

---

## Workflow

### 1. Inspect Parent Epic & State
- Fetch the parent issue via `gh issue view <epic-number>`.
- Parse the `Execution Plan & Progress` checklist.
- Identify the **next unblocked slice**:
  - Check that all prerequisite slices (`Depends on: #<prev>`) have been merged.
  - If a prerequisite slice is still in review/open, do NOT proceed to the next dependent slice.

### 2. Provision Isolated Git Worktree
For the next unblocked slice (e.g. Issue `#<id>`):
1. Fetch latest `main`:
   ```bash
   git fetch origin main
   ```
2. Create dedicated worktree using the deterministic naming standard:
   ```bash
   git worktree add .worktrees/issue-<id> -b feat/issue-<id>-<slug> origin/main
   ```
3. Ensure `.worktrees/` is listed in `.gitignore`.

### 3. Dispatch Executor Subagent
Invoke an executor subagent pointing strictly to the worktree path:
- **Target Directory**: `.worktrees/issue-<id>`
- **Assigned Task**: "Execute issue `#<id>` end-to-end using `/implement <id>` guidelines (TDD, clean boundaries, passing tests, submit PR)."
- **Instructions**: The executor must run all commands (lint, test, build, git commit, gh pr create) exclusively inside `.worktrees/issue-<id>`.

### 4. Review & Iterative Feedback Loop
Once the executor submits the PR (or signals completion):
1. **Verification**: Verify the implementation in `.worktrees/issue-<id>`:
   - Run test suite and linters (`make test`, `make lint`).
   - If UI or user-facing: test locally or review screenshots/PR guide.
2. **Handle Feedback / Fixes**:
   - If adjustments, styling polishes, or bug fixes are required: dispatch instructions back to the executor subagent in that same worktree.
   - Commit atomic fixes to the same branch until all acceptance criteria are met.
3. **Merge Gate**:
   - Merge the PR to `main` (either after developer approval or via `gh pr merge --squash --delete-branch`).

### 5. Deterministic Cleanup & Advance
Once the PR is merged into `main`:
1. Clean up the worktree:
   ```bash
   git worktree remove .worktrees/issue-<id> --force
   git branch -D feat/issue-<id>-<slug> 2>/dev/null || true
   git worktree prune
   ```
   *(Or run `bash <skill-dir>/scripts/cleanup-worktrees.sh`)*
2. Update the parent Epic checklist:
   - Edit the parent issue so the completed slice is checked: `- [x] <k>. #<id>`.
3. Check the next slice in the graph. If more slices remain, loop back to **Step 2**.
4. When all slices are checked `[x]`, close the parent Epic.
