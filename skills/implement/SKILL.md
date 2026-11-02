---
name: implement
description: >-
  Implements a GitHub issue on a feature branch, enforcing clean code,
  no redundant comments, and opening a PR with a human-centric reviewer guide.
---

# /implement

Implement a GitHub issue end-to-end and submit a reviewer-optimized PR.

## Workflow

1. **Context**: 
   - Fetch issue via `gh issue view <issue-number>`.
   - Inspect `AGENTS.md` and repo architecture rules.
   - **Detect Target Integration Base**: Check if the issue body specifies an integration branch (e.g., `- **Integration Branch**: epic/issue-<epic-number>-<slug>`). If present, PR target base is that integration branch; otherwise, target `main`.

2. **Branch & Workspace Setup**:
   - **If inside an isolated worktree** (e.g. `.worktrees/issue-<number>` dispatched by `/orchestrate`): The feature branch is already provisioned and checked out. Work directly on the current branch.
   - **If standalone in the main workspace**:
     - If an Integration Branch was detected:
       ```bash
       git fetch origin <integration-branch>
       git checkout -b feat/issue-<number>-<short-name> origin/<integration-branch>
       ```
     - If standalone (no Epic):
       ```bash
       git checkout -b feat/issue-<number>-<short-name> from clean, updated main
       ```

3. **Standards**:
   - **Zero Redundant Comments**: Code must be self-documenting. Reserve comments strictly for non-obvious business rules or safety constraints.
   - **Meaningful Tests (No Vanity Tests)**: Never write tautological tests that test nothing. Cover real edge cases, state invariants, and failure paths. Refactor existing test tables rather than appending redundant tests; eliminate dead test code ruthlessly.
   - **Architecture & Boundaries**: Follow the repository's native architectural style (e.g. Hexagonal, Clean, MVC, Feature-based).
   - **Concurrency & Safety**: Context propagation on all I/O; proper synchronization on shared mutable state.
   - **Errors & Logs**: Use idiomatic sentinel/domain errors and structured logging. Never use raw prints for runtime logs.

4. **Commits**: Make iterative, atomic Conventional Commits (`type(scope): message`).

5. **Verify**: Ensure project test suite passes (with race/concurrency checks enabled) and build succeeds.

6. **Pull Request**:
   - Push branch to remote.
   - Run `gh pr create`:
     - If part of an Epic: `gh pr create --base <integration-branch>`
     - If standalone: `gh pr create --base main`
   - Adapt the template below dynamically to match the project's real stack and architecture:

```markdown
## 🎯 What & Why
<2-3 sentence executive summary of problem and solution>
Closes #<issue-number>

## 🗺️ Recommended Review Order
*Order files by cognitive dependency (e.g., core models/logic first, then services/adapters, then wiring/UI, tests last) rather than the alphabetical git diff:*
1. [`path`](link) — <why to read first>
2. [`path`](link) — <why to read next>

## ⚠️ Business-Sensitive & Critical Areas
*Highlight high-risk sections (safety rules, concurrency locks, security/auth, financial logic, data migrations). Note "Low risk" if none:*
- **`Symbol`** ([`file#L10`](link)): Why it's critical, potential failure mode, and what to verify.

## 🛠️ On-Call & Debugging Cheat Sheet
*Triage guidance if an incident occurs in production:*
- **Key Log Signatures**: Relevant error/warning logs to grep for.
- **Diagnostic Check**: (Relevant health check, CLI command, or query for triage)

## 🧪 Verification & Proof
- [x] Test suite and race checks passed.
- [x] Build succeeded.
- [x] Verification output:
  ```
  <sample test output or CLI response>
  ```
```
