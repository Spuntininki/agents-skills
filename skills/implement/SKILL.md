---
name: implement
description: >-
  Implements a GitHub issue on a feature branch, enforcing clean code,
  meaningful tests, and opening a PR with a reviewer guide.
---

# /implement

Implement a GitHub issue end-to-end and submit a reviewer-optimized PR.

## Workflow

1. **Context & Target Base**:
   - Fetch issue: `gh issue view <issue-number>`. Inspect repo rules (`AGENTS.md`).
   - If issue body contains `- **Integration Branch**: <branch>`, set PR base to that branch; otherwise target `main`.

2. **Workspace Setup**:
   - **Inside isolated worktree (`.worktrees/issue-<id>`)**: Work directly on the existing checked-out branch.
   - **Standalone run**:
     ```bash
     git fetch origin <base-branch>
     git checkout -b feat/issue-<number>-<short-name> origin/<base-branch>
     ```

3. **Code & Test Standards**:
   - **Clean Code**: Self-documenting, zero redundant comments (comments strictly for non-obvious business/safety rules). Safe concurrency, proper context propagation, idiomatic structured errors/logs.
   - **Meaningful Tests**: No tautological/vanity tests. Test real invariants, edge cases, and failure modes.

4. **Commits & Verification**:
   - Make atomic Conventional Commits (`type(scope): message`).
   - Verify: test suite passes (with race/concurrency checks) and build succeeds.

5. **Pull Request**:
   - Push branch and run `gh pr create --base <base-branch>` using this template:

```markdown
## 🎯 What & Why
<2-3 sentence executive summary. Closes #<issue-number>>

## 🗺️ Recommended Review Order
*Order files by cognitive dependency (models -> services -> wiring -> tests):*
1. [`path`](link) — <why to read first>

## ⚠️ Critical Areas & Edge Cases
*High-risk sections (concurrency, security, data migrations, or "Low risk"):*
- **`Symbol`** ([`file#L10`](link)): <Failure mode and verification advice>

## 🧪 Verification & Proof
- [x] Test suite and linters passed.
- Output: `<sample test output or verification command>`
```
