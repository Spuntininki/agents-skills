---
name: revise
description: >-
  Evaluates code review feedback, conducts peer technical dialogue on trade-offs,
  and delegates verified implementation to /implement on the existing PR.
---

# /revise

Evaluate code review feedback, debate technical trade-offs, and synthesize an actionable revision specification for `/implement`.

Rather than duplicating coding standards, `/revise` serves as the **Code Review Triage & Dialogue Engine**, handing off implementation directly to `/implement` while keeping the original PR updated.

```
                  ┌───────────────┐
Feature Planning: │    /refine    │ ───┐
                  └───────────────┘    │
                                       ▼
                  ┌───────────────┐ ┌───────────────┐
Review Revisions: │    /revise    │─┤  /implement   │ ──> [PR Updated & Verified]
                  └───────────────┘ └───────────────┘
```

## Guiding Principles

- **Peer Dialogue over Sycophancy**: Code review is a peer engineering dialogue, not mindless obedience. Critically evaluate suggestions against system invariants, concurrency safety, and performance. If a suggestion introduces risks, weakens error handling, or undoes an intentional design decision, articulate the rationale, explain the trade-off, and debate or propose alternatives before modifying code.
- **Review-Driven Business & Behavioral Alignment**: Validated review feedback (business logic corrections, missing edge cases, invariant adjustments) must be fully addressed across domain models and tests.
- **Single Implementation Engine**: Delegate all code modifications, linting, test verification, and commit execution to `/implement`. Do not maintain duplicate coding standards.
- **Original PR & Worktree Target**: Revisions belong to the original PR and issue. Never create redundant issues. Work directly in the active worktree (`.worktrees/issue-<id>`) or provision an isolated worktree for the PR branch.

---

## Workflow

### 1. Identify Target PR & Workspace
Accept one or more of:
- PR number or URL: `/revise 14`
- Optional inline instructions: `/revise 14 "align discount with enterprise tier"`
- If no argument is provided, detect the current active branch or open PR.

**Query Target PR Details:**
```bash
PR_DATA=$(gh pr view <pr-number> --json headRefName,baseRefName,state,number)
HEAD_BRANCH=$(echo "$PR_DATA" | jq -r .headRefName)
BASE_BRANCH=$(echo "$PR_DATA" | jq -r .baseRefName)
PR_STATE=$(echo "$PR_DATA" | jq -r .state)
```

**Deterministic Workspace Provisioning (Worktree-First):**
Never dirty the root workspace. Always resolve to an isolated worktree directory:
```bash
# 1. Reuse existing worktree if still active
if [ -d ".worktrees/issue-<id>" ]; then
  cd .worktrees/issue-<id>
elif [ -d ".worktrees/pr-<pr-number>" ]; then
  cd .worktrees/pr-<pr-number>

# 2. If PR is OPEN and worktree was pruned or absent: provision a fresh isolated worktree
elif [ "$PR_STATE" = "OPEN" ]; then
  git fetch origin "$HEAD_BRANCH"
  git worktree add .worktrees/pr-<pr-number> "$HEAD_BRANCH"
  cd .worktrees/pr-<pr-number>

# 3. If PR is already MERGED into the Epic branch: branch from Epic base for follow-up fix
elif [ "$PR_STATE" = "MERGED" ]; then
  git fetch origin "$BASE_BRANCH"
  git worktree add .worktrees/rev-pr-<pr-number> -b fix/rev-pr-<pr-number> origin/"$BASE_BRANCH"
  cd .worktrees/rev-pr-<pr-number>
fi
```

### 2. Ingest & Evaluate Review Feedback (Technical Dialogue)
Retrieve all open reviews and inline comments from GitHub:
```bash
# Fetch PR details and top-level reviews
gh pr view <pr-number> --json title,body,reviews,comments

# Fetch specific inline diff comments
gh api repos/:owner/:repo/pulls/<pr-number>/comments \
  --jq '.[] | {path: .path, line: .line, body: .body, user: .user.login}'
```

Combine GitHub review comments with any additional instructions provided in the chat.

**Classify & Evaluate Each Item Critically:**
- **Category A (Direct Corrections & Fixes)**: Validated bug, missed edge case, typo, or requested business rule adjustment $\rightarrow$ Queue for implementation.
- **Category B (Design Disagreements & High-Risk Suggestions)**: If the reviewer's suggestion introduces performance regressions, concurrency race conditions, breaks external contracts, or undoes an intentional design decision $\rightarrow$ **Debate before coding**:
  > *"Regarding the suggestion on `path/to/file#L40`: I originally implemented approach X because of [rationale/invariant]. If we switch to [suggestion], [trade-off/risk] would occur. We could also consider [alternative C]. How would you prefer to proceed?"*
  Wait for developer confirmation on Category B items before making controversial changes.

### 3. Synthesize Revision Specification & Delegate to /implement
Synthesize the agreed-upon changes into a clear Revision Specification:
```markdown
## 🛠️ Revision Specification for PR #<pr-number>
- **Target Branch**: `<head-branch>`
- **Scope of Revisions**:
  1. [`file`](path#L10): <Specific correction or business rule change>
  2. [`tests`](path): <Living test to update or add verifying the change>
- **Invariants & Safety Rules**: <Key constraints to maintain>
```

Dispatch an executor subagent (or execute directly in current worktree) invoking `/implement`:
> "Implement the Revision Specification above on branch `<head-branch>`. Adhere to clean code standards (no vanity tests, zero redundant comments, pinned dependencies), run project test suite, and commit atomically with `refactor(<scope>): address review feedback ...`."

### 4. Post Summary on PR & Cleanup
Once `/implement` finishes verification and pushes to `<head-branch>`:
```bash
# Post summary comment resolving review items
gh pr comment <pr-number> --body "$(cat << 'EOF'
## 🛠️ Revisions Applied

Addressed review feedback:
- **`path/to/file.ext`**: <Summary of change made>
- **`tests/path_test.ext`**: <Updated test verifying the review point>

All tests and lint checks passing. Ready for re-review!
EOF
)"

# If a temporary worktree was created dynamically for this revision, remove it
cd - >/dev/null
git worktree remove .worktrees/pr-<pr-number> --force 2>/dev/null || true
```
