---
name: revise
description: >-
  Addresses code review feedback and requested changes on an open pull request or branch,
  applying surgical fixes, running verification, and updating the PR.
---

# /revise

Incorporate code review feedback, peer suggestions, or requested changes into an existing pull request or branch.

Unlike a bug diagnosis or full rewrite, `/revise` is surgical: it addresses specific review comments while maintaining architectural boundaries, existing conventions, and test coverage.

## Guiding Principles

- **Review-Driven Behavioral & Business Alignment**: Code reviews frequently uncover incorrect domain assumptions, missing edge cases, flawed state transitions, or misaligned business rules. The agent MUST fully implement whatever behavioral, business, or architectural corrections the reviewer requests—modifying domain entities, use cases, and tests as deeply as needed to satisfy the business intent.
- **Zero Unsolicited Scope Creep**: The restriction is strictly against *gratuitous, unrequested changes* (e.g. reformatting untouched files, refactoring unrelated endpoints, changing code style elsewhere, or upgrading unrelated dependencies). Any change directly required to fulfill the reviewer's requested behavior is 100% in scope.
- **Dual-Source Review Ingestion**: Ingest feedback seamlessly from both **GitHub PR reviews/comments** (`gh api`, `gh pr view`) and **in-chat developer instructions**.
- **Context & Workspace Awareness**:
  - If a worktree exists for this slice (`.worktrees/issue-<id>`), work directly inside it.
  - If it is a standalone PR or branch, checkout the branch (`gh pr checkout <pr-number>`).
  - If the slice was already merged into an Epic branch, create a dedicated revision branch targeting the Epic branch (`fix/review-issue-<id>`).
- **Living Test Synchronization**: When altering behavior or business rules based on review feedback, always update or add corresponding unit/integration tests to serve as living proof of the corrected behavior.
- **Subagent Execution on Original Issue/PR**: Code review revisions belong to the original issue and PR—never create redundant issues for review feedback. Execute revisions inside an isolated executor subagent operating in the target worktree. This prevents build logs, test outputs, and compiler noise from polluting the orchestrator's conversation context while updating the original PR branch directly.
- **Traceable Atomic Commits**: Commit changes with conventional messages referencing the review (e.g. `refactor(auth): address review feedback on token expiration` or `fix(order): align discount business rule with enterprise tier`), push to the PR branch, and update the PR with a summary of changes.

---

## Workflow

### 1. Identify Target PR & Workspace
Accept one or more of:
- PR number or URL: `/revise 14`
- Optional inline instructions: `/revise 14 "rename DTO to CustomerPayload and add invalid domain test"`
- If no argument is provided, detect the current active branch or open PR.

> [!TIP]
> When invoked within an orchestration or multi-task session, dispatch a dedicated executor subagent into the worktree to perform `/revise`. This keeps the parent session's context window clean while updating the original PR in place.

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

### 2. Ingest Review Feedback
Retrieve all open reviews and inline comments from GitHub:
```bash
# Fetch PR details and top-level reviews
gh pr view <pr-number> --json title,body,reviews,comments

# Fetch specific inline diff comments
gh api repos/:owner/:repo/pulls/<pr-number>/comments \
  --jq '.[] | {path: .path, line: .line, body: .body, user: .user.login}'
```

Combine GitHub review comments with any additional instructions provided in the chat. Formulate an actionable checklist of review items:
- [ ] Item 1: `path/to/file.ext` — <Specific requested change>
- [ ] Item 2: `path/to/file.ext` — <Specific requested change>

### 3. Apply Revisions & Behavioral Corrections
- For each review item:
  - Understand the reviewer's intent: whether it is a business rule correction, edge-case validation, domain invariant alignment, architectural adjustment, or structural refinement.
  - Implement all changes required across the affected domain entities, use cases, and tests to satisfy the reviewer's requirement completely.
  - Do NOT make gratuitous, unrequested alterations to unrelated files or unaffected code.

### 4. Verify & Test
Run the relevant test suite and linters to ensure zero regressions:
```bash
# Run targeted tests for modified module
<test-command-for-project>

# Run linter
<lint-command-for-project>
```

### 5. Commit & Push
Commit with a clear, conventional message describing the review resolution:
```bash
git add <modified-files>
git commit -m "refactor(<scope>): address review feedback regarding <summary>"

# If working on an open PR: push directly to update the PR
if [ "$PR_STATE" = "OPEN" ]; then
  git push origin "$HEAD_BRANCH"

# If PR was already merged into the Epic: push follow-up branch and open a quick revision PR
elif [ "$PR_STATE" = "MERGED" ]; then
  git push origin fix/rev-pr-<pr-number>
  gh pr create --base "$BASE_BRANCH" --head fix/rev-pr-<pr-number> \
    --title "fix: review adjustments for PR #<pr-number>" \
    --body "Applies review adjustments requested on merged PR #<pr-number>."
fi
```

### 6. Notify Reviewer / Post Summary & Cleanup
Post a concise summary comment on the PR detailing how each review item was resolved:
```bash
gh pr comment <pr-number> --body "$(cat << 'EOF'
## 🛠️ Revisions Applied

Addressed review feedback in commit `<commit-hash>`:
- **`path/to/file.ext`**: <Summary of change made>
- **`tests/path_test.ext`**: <Added or updated test verifying the review point>

All tests and lint checks passing. Ready for re-review!
EOF
)"

# If a temporary worktree was created exclusively for this revision, remove it
cd - >/dev/null
git worktree remove .worktrees/pr-<pr-number> --force 2>/dev/null || true
```
