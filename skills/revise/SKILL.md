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

- **Surgical Execution (Anti-Rewrite)**: Touch *only* the specific files, lines, and abstractions flagged by the reviewer. Never introduce unrequested refactorings, change surrounding formatting, or alter unrelated business logic.
- **Dual-Source Review Ingestion**: Ingest feedback seamlessly from both **GitHub PR reviews/comments** (`gh api`, `gh pr view`) and **in-chat developer instructions**.
- **Context & Workspace Awareness**:
  - If a worktree exists for this slice (`.worktrees/issue-<id>`), work directly inside it.
  - If it is a standalone PR or branch, checkout the branch (`gh pr checkout <pr-number>`).
  - If the slice was already merged into an Epic branch, create a dedicated revision branch targeting the Epic branch (`fix/review-issue-<id>`).
- **Regression Prevention**: Always run existing project tests and linters to verify that incorporating the review feedback did not break existing behavior.
- **Traceable Atomic Commits**: Commit changes with conventional messages referencing the review (e.g. `refactor(auth): address review feedback on token expiration`), push to the PR branch, and update the PR with a summary of changes.

---

## Workflow

### 1. Identify Target PR & Workspace
Accept one or more of:
- PR number or URL: `/revise 14`
- Optional inline instructions: `/revise 14 "rename DTO to CustomerPayload and add invalid domain test"`
- If no argument is provided, detect the current active branch or open PR.

Determine workspace location:
```bash
# Case A: Inside an active orchestrate worktree
cd .worktrees/issue-<id>

# Case B: Standalone PR / branch
gh pr checkout <pr-number>
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

### 3. Apply Surgical Modifications
- For each review item:
  - Open the exact file and lines referenced.
  - Apply the requested changes (e.g. renaming, edge-case validation, tightening types, extracting helper).
  - Do NOT touch unrelated code.

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
git push origin <branch-name>
```

### 6. Notify Reviewer / Post Summary
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
```
