---
name: orchestrate
description: >-
  Supervises and executes multi-issue epics using isolated git worktrees,
  concurrent subagent dispatch for parallel slices, an Epic Integration Branch,
  and deterministic workspace cleanup.
---

# /orchestrate

Supervise, coordinate, and execute multi-issue epics end-to-end.

Dispatches executor subagents into isolated git worktrees against an **Epic Integration Branch**, manages dependency ordering, leverages **concurrent dispatch for parallel slices**, enforces iterative verification before merge, guarantees deterministic workspace cleanup, and delivers a **single atomic deployment to production**.

## Guiding Principles

- **Epic Integration Branch (Single Atomic Deployment)**:
  - All child slices branch from and merge into a dedicated integration branch: `epic/issue-<epic-number>-<slug>`.
  - Child PRs target this epic branch (`--base epic/issue-...`). This prevents multiple partial deployments to the VPS / production while preserving micro-PR reviewability.
  - Only when all slices in the epic are complete is a single final PR merged into `main`, triggering one atomic CD build, migration gate, and rollout.
- **Deterministic Worktree Isolation (`.worktrees/issue-<number>`)**:
  - Every active child slice executes in its own dedicated git worktree located at `.worktrees/issue-<number>` on a branch named `feat/issue-<number>-<slug>` (or `fix/issue-...`).
  - Completely isolates filesystem changes, dependencies, test databases, and git operations between concurrent agents.
- **Concurrent Dispatch for Parallel Slices**:
  - Slices marked as `Parallel ⚡` whose dependencies are met can be provisioned and dispatched **simultaneously**.
  - Review throughput: The developer reviews and merges PRs asynchronously as each subagent finishes, without waiting for the slowest task.
- **Rebase on Epic Integration Branch**:
  - When a parallel PR merges into the epic branch, any sibling concurrent worktrees that are still active pull the latest changes (`git fetch origin <epic-branch> && git rebase origin/<epic-branch>`) to ensure integration continuity.
- **Iterative Feedback Loop (Anti-One-Shot SDD)**:
  - Any bug, regression, or adjustment uncovered during review MUST be resolved inside that slice's worktree before merging into the epic branch.
  - Never open new issues for bugs introduced within the current unmerged slice.
- **Deterministic Cleanup**:
  - Once a slice's PR is merged into the epic branch, its worktree and local branch are purged immediately (`git worktree remove` + `git branch -D` + `git worktree prune` or `scripts/cleanup-worktrees.sh`).
- **Tracking Issue as State Machine**:
  - The parent Epic checklist (`- [ ] ...`) is the single source of truth for execution state.
  - As each child PR merges, the orchestrator updates the item (`- [x] ...`), unblocking downstream slices.

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

### 2. Identify Unblocked Slices (Serial vs. Parallel)
Parse the parent issue's `Execution Plan & Progress` checklist:
- Identify all pending slices (`- [ ]`).
- For each pending slice, verify if its dependencies (`Depends on: #<prev>`) are marked `[x]` (or "None").
- Group unblocked slices:
  - **Single Serial Slice (`Mode: Serial 🔒`)**: Dispatch exclusively.
  - **Multiple Parallel Slices (`Mode: Parallel ⚡`)**: If multiple unblocked slices in the active phase are marked parallel, **provision and dispatch them concurrently**.

### 3. Provision Isolated Git Worktree(s)
For each unblocked slice `#<id>` to be dispatched:
1. Update local reference to the epic branch:
   ```bash
   git fetch origin epic/issue-<epic-number>-<slug>
   ```
2. Create dedicated worktree branched from the epic integration branch:
   ```bash
   git worktree add .worktrees/issue-<id> -b feat/issue-<id>-<slug> origin/epic/issue-<epic-number>-<slug>
   ```
3. Ensure `.worktrees/` is listed in `.gitignore`.

### 4. Dispatch Executor Subagents
Invoke executor subagent(s) pointing strictly to their respective worktrees:
- **Target Directory**: `.worktrees/issue-<id>`
- **Assigned Task**:
  > "Implement issue `#<id>` using `/implement <id>` guidelines (TDD, clean boundaries, passing tests). You are working inside an isolated git worktree already on the feature branch. When creating the pull request, target the integration branch: `gh pr create --base epic/issue-<epic-number>-<slug>`."
- If multiple slices are parallel, invoke the executor subagents concurrently.

### 5. Review & Asynchronous Feedback Loop
As executor subagents complete their work and submit PRs against the epic branch:
1. **Verification**: Verify implementation in `.worktrees/issue-<id>`:
   - Run test suite and linters (`make test`, `make lint`).
   - Review PR diff.
2. **Handle Feedback / Fixes**:
   - If adjustments are required: message the executor subagent in that same worktree to make atomic fixes.
3. **Merge Gate**:
   - Merge PR into the epic integration branch:
     ```bash
     gh pr merge <pr-number> --squash --delete-branch
     ```
4. **Sync Active Sibling Worktrees (for Parallel Tasks)**:
   - If sibling worktrees are still working in parallel on other issues, sync their branches against the updated epic branch:
     ```bash
     git -C .worktrees/issue-<sibling-id> fetch origin epic/issue-<epic-number>-<slug>
     git -C .worktrees/issue-<sibling-id> rebase origin/epic/issue-<epic-number>-<slug>
     ```

### 6. Deterministic Cleanup & Advance
Once a slice is merged into the epic branch:
1. Clean up the finished worktree:
   ```bash
   git worktree remove .worktrees/issue-<id> --force
   git branch -D feat/issue-<id>-<slug> 2>/dev/null || true
   git worktree prune
   ```
   *(Or run `bash <skill-dir>/scripts/cleanup-worktrees.sh`)*
2. Update the parent Epic checklist:
   - Edit the parent issue so the completed slice is checked: `- [x] ... #<id>`.
3. If pending slices remain in the checklist, return to **Step 2**.

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
   - The CD pipeline triggers **once**: building Docker images, pushing to GHCR, updating Kustomize manifests, and rolling out atomically to the VPS cluster.
   - Close the parent Epic on GitHub.
   - Delete the remote epic branch: `git push origin --delete epic/issue-<epic-number>-<slug>`.
