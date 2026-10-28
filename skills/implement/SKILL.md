---
name: implement
description: >-
  Implements a GitHub issue on a feature branch, enforcing clean code,
  no redundant comments, and opening a PR with a human-centric reviewer guide.
---

# Implement

Implement a GitHub issue end-to-end and submit a reviewer-optimized PR.

## Workflow

1. **Context**: Fetch issue via `gh issue view <issue-number>`. Inspect `AGENTS.md` and repo architecture rules.
2. **Branch**: Inspect the current checkout and working tree first. Preserve existing changes and follow repository rules for the base branch and worktrees. Use `codex/issue-<number>-<short-name>` for a new branch unless the user or repository specifies another prefix. Do not assume the base branch is `main`.
3. **Standards**:
   - **Zero Redundant Comments**: Code must be self-documenting. Reserve comments strictly for non-obvious business rules or safety constraints.
   - **Meaningful Tests (No Vanity Tests)**: Never write tautological tests that test nothing. Cover real edge cases, state invariants, and failure paths. Refactor existing test tables rather than appending redundant tests; eliminate dead test code ruthlessly.
   - **Architecture & Boundaries**: Follow the repository's native architectural style (e.g. Hexagonal, Clean, MVC, Feature-based).
   - **Concurrency & Safety**: Context propagation on all I/O; proper synchronization on shared mutable state.
   - **Errors & Logs**: Use idiomatic sentinel/domain errors and structured logging. Never use raw prints for runtime logs.
4. **Commits**: Follow repository and user authorization rules. Commit or push only when explicitly requested; otherwise leave the implementation and verification results ready for review. When authorized, use atomic Conventional Commits (`type(scope): message`).
5. **Verify**: Follow repository testing requirements, including TDD where required. Run the required tests, lint, and build checks; use race/concurrency checks when supported and relevant. Report actual results and any checks that could not run.
6. **Pull Request**: When commit/push and PR publication are authorized, push the branch and run `gh pr create --body-file <file>`. Attach every created PR to the current chat with the Codex `attach_artifact` tool when available. Otherwise provide the review-ready local changes and a proposed PR description. Adapt the template below dynamically to match the project's real stack and architecture (do not force non-existent layers or irrelevant commands):

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
- <Actual test results, including relevant concurrency checks when available.>
- <Actual lint/build results; identify skipped or unavailable checks.>
- Verification output:
  ```
  <sample test output or CLI response>
  ```
```
