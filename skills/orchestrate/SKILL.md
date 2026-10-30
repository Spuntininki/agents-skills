---
name: orchestrate
description: >-
  Supervises and executes multi-issue epics using isolated git worktrees,
  an Epic Integration Branch for atomic deployment, iterative feedback loops,
  and subagent executors.
---

# /orchestrate

Supervise, coordinate, and execute multi-issue epics end-to-end. 

Dispatches executor subagents into isolated git worktrees against an **Epic Integration Branch**, manages dependency ordering, enforces iterative verification before merge, guarantees deterministic workspace cleanup, and delivers a **single atomic deployment to production**.

## Guiding Principles

- **Epic Integration Branch (Single Atomic Deployment)**:
  - All child slices branch from and merge into a dedicated integration branch: `epic/issue-<epic-number>-<slug>`.
  - Child PRs target this epic branch (`--base epic/issue-...`). This prevents triggering multiple partial deployments to the VPS / production while preserving micro-PR reviewability.
  - Only when all slices in the epic are complete is a single final PR merged into `main`, triggering one atomic CD build, migration gate, and rollout.
- **Deterministic Worktree Isolation (`.worktrees/issue-<number>`)**:
  - Every child slice executes in its own dedicated git worktree located at `.worktrees/issue-<number>` on a branch named `feat/issue-<number>-<slug>` (or `fix/issue-<number>-<slug>`).
  - Completely isolates filesystem changes, test databases, node_modules, and git operations from the main workspace and other concurrent agents.
- **Iterative Feedback Loop (Anti-One-Shot SDD)**:
  - Real-world development is iterative, not one-shot. Any bug, edge case, regression, or visual/behavioral adjustment introduced during the slice's implementation MUST be fixed inside that slice's worktree before merging into the epic branch.
  - Never open new issues for bugs introduced within the current unmerged slice. Keep refining the slice until all tests pass and verification criteria are satisfied.
  - Only genuine scope creep (net-new requirements not in the slice's spec) should be deferred to a separate issue.
- **Deterministic Cleanup**:
  - Once a slice's PR is merged into the epic branch, its worktree and local branch are purged immediately (`git worktree remove` + `git branch -D` + `git worktree prune`).
  - Run `scripts/cleanup-worktrees.sh` to safely purge any lingering merged worktrees.
- **Tracking Issue as State Machine**:
  - The parent Epic checklist (`- [ ] 1. #<child> ...`) is the single source of truth for execution state.
  - As each child PR merges, the orchestrator checks off the item (`[x] 1. #<child>`), unblocking downstream slices.
- **Strict Role Separation**:
  - The orchestrator supervises the macro execution graph, epic branch, and state.
  - Executor subagents perform the actual implementation (`/implement`) inside their assigned worktree.

---

## Workflow

### 1. Inspect Parent Epic & Initialize Integration Branch
1. Fetch parent issue via `gh issue view <epic-number>`.
2. Extract the target integration branch: `epic/issue-<epic-number>-<slug>`.
3. Ensure the integration branch exists:
   - If not yet created on remote:
     ```bash
     git fetch origin main
     git checkout -b epic/issue-<epic-number>-<slug> origin/main
     git push -u origin epic/issue-<epic-number>-<slug>
     git checkout main
     ```
   - If already existing:
     ```bash
     git fetch origin epic/issue-<epic-number>-<slug>
     ```

### 2. Identify Next Unblocked Slice
- Parse the parent issue's `Execution Plan & Progress` checklist.
- Find the next pending slice (`- [ ] <k>. #<id>`).
- Verify its dependencies (`Depends on: #<prev>`) are marked `[x]` (merged into the epic branch).
- If a dependency is still open or in review, halt and await completion.

### 3. Provision Isolated Git Worktree from Epic Branch
For the unblocked slice `#<id>`:
1. Update local reference:
   ```bash
   git fetch origin epic/issue-<epic-number>-<slug>
   ```
2. Create dedicated worktree branched from the epic integration branch:
   ```bash
   git worktree add .worktrees/issue-<id> -b feat/issue-<id>-<slug> origin/epic/issue-<epic-number>-<slug>
   ```
3. Ensure `.worktrees/` is listed in `.gitignore`.

### 4. Dispatch Executor Subagent
Invoke an executor subagent pointing strictly to the worktree path:
- **Target Directory**: `.worktrees/issue-<id>`
- **Assigned Task**: "Implement issue `#<id>` using `/implement <id>` guidelines (TDD, clean boundaries, passing tests). When creating the pull request, target the integration branch: `gh pr create --base epic/issue-<epic-number>-<slug>`."
- **Instructions**: The executor must run all commands (lint, test, build, git commit, gh pr create) exclusively inside `.worktrees/issue-<id>`.

### 5. Review & Iterative Feedback Loop
Once the executor submits the PR against the epic branch:
1. **Verification**: Verify implementation in `.worktrees/issue-<id>`:
   - Run test suite and linters (`make test`, `make lint`).
   - Test locally or review PR diff.
2. **Handle Feedback / Fixes**:
   - If adjustments or bug fixes are required: dispatch instructions back to the executor subagent in that same worktree.
   - Commit atomic fixes to the same branch until all acceptance criteria are met.
3. **Merge Gate**:
   - Merge PR into the epic branch:
     ```bash
     gh pr merge <pr-number> --squash --delete-branch
     ```

### 6. Deterministic Cleanup & Advance
Once merged into the epic branch:
1. Clean up the child worktree:
   ```bash
   git worktree remove .worktrees/issue-<id> --force
   git branch -D feat/issue-<id>-<slug> 2>/dev/null || true
   git worktree prune
   ```
   *(Or run `bash <skill-dir>/scripts/cleanup-worktrees.sh`)*
2. Update the parent Epic checklist:
   - Edit the parent issue so the completed slice is checked: `- [x] <k>. #<id>`.
3. If pending slices remain in the checklist, loop back to **Step 2**.

### 7. Atomic Release Gate (Deploy to Production)
When all slices in the parent Epic are checked `[x]`:
1. Open the final release pull request from the epic branch into `main`:
   ```bash
   gh pr create --base main --head epic/issue-<epic-number>-<slug> \
     --title "feat: <epic-title>" \
     --body "## 🎯 Summary
   All child slices completed and verified. Closes #<epic-number>."
   ```
2. Once the final PR is reviewed and merged into `main`:
   - The CD pipeline triggers **once**: building Docker images, pushing to GHCR, updating Kustomize manifests, and rolling out atomically to the k3s VPS cluster.
   - Close the parent Epic on GitHub.
   - Delete the remote epic branch: `git push origin --delete epic/issue-<epic-number>-<slug>`.
