---
name: slice
description: >-
  Breaks down a feature idea or large GitHub issue into small, vertically sliced
  micro-issues (≤ 200-300 lines of diff budget each) to prevent review fatigue
  and keep PRs fast and easy to verify.
---

# /slice

Break down complex feature ideas or large GitHub issues into small, independent, vertically sliced micro-issues with strict diff budgets (≤ 200–300 lines of code change per issue). Prevents reviewer fatigue and enables fast, confidence-inspiring PR reviews.

## Guiding Principles

- **Diff Budget Rule**: No individual issue should require more than ~200–300 lines of non-boilerplate code changes or modify more than 3–4 core files.
- **Vertical Slicing over Horizontal Layers**: Each slice delivers verifiable, testable behavior end-to-end where possible (e.g., Core + Model + Unit Test; then API + Schema; then UI/Consumer). Avoid purely speculative layers that cannot be independently tested or merged.
- **Micro-PR Mindset**: If an issue requires a database migration, core service logic, API endpoints, worker tasks, and frontend UI, it MUST be split into multiple smaller issues.
- **Cohesion over Arbitrary Fragmentation**:
  - Slicing applies to **issues, features, and PRs**, NOT to artificially chopping up coherent functions.
  - Do NOT fragment clear, linear functions into artificial micro-helpers just to satisfy an arbitrary line-count metric (this creates fragmented "lasagna / spaghetti" code). A cohesive 30–50 line function that reads clearly top-to-bottom is far superior to multiple shallow one-off helpers.
  - Keep cyclomatic complexity low using guard clauses and early returns rather than deep `if/else` nesting.
  - Eliminate redundant comments; let well-named domain concepts speak for themselves.

## Workflow

### 1. Input Analysis
Determine the input type:
- **Case A: Raw Feature Idea / Prompt** (e.g. `/slice Add user notification preference and email alerts`):
  - Inspect codebase architecture, models, schemas, and directory structure.
  - Estimate the affected layers (DB, core logic, API, background workers, frontend/bots).
- **Case B: Existing GitHub Issue** (e.g. `/slice 18` or `/slice https://github.com/.../issues/18`):
  - Fetch issue details via `gh issue view <issue-number>`.
  - Analyze the existing scope, implementation plan, and acceptance criteria.
  - Evaluate estimated diff size against the ~200–300 line diff budget.

### 2. Propose Vertical Slices
Before creating issues on GitHub, present the proposed breakdown to the developer:
- Explain why the task should be divided (e.g. multi-layer impact, diff budget exceedance).
- Present 2 to 4 vertical slices, ordered by cognitive dependency:
  - **Slice 1 (Foundation/Core)**: Data models, migrations, core domain service, unit tests. (Diff budget: ~200 lines).
  - **Slice 2 (Transport/Service)**: API endpoints, background workers/tasks, integration tests. (Diff budget: ~200 lines).
  - **Slice 3 (Presentation/Consumer)**: Web UI components, Telegram bot commands, client SDK generation. (Diff budget: ~250 lines).
- For each slice, define:
  - Conventional commit title (`type(scope): imperative summary`).
  - Clear scope boundaries: **What is IN scope** vs. **What is explicitly OUT of scope** (deferred to next slice).
  - Concrete acceptance criteria (checkboxes).
- Ask for the developer's confirmation or adjustments.

### 3. Create / Update GitHub Issues
Once confirmed by the developer:
- **If slicing an existing issue (Case B)**:
  - Convert the existing issue into an **Epic / Tracking Issue** using `gh issue edit <issue-number> --body ...`:
    - Add a progress checklist linking to the child issues.
    - Retain overall architectural context and motivation.
  - Create child issues via `gh issue create`:
    - Title: Conventional commit format (`feat(...)`, `fix(...)`).
    - Labels: matching repo labels (`enhancement`, `bug`).
    - Body: Problem statement, IN/OUT scope boundaries, acceptance criteria, and link to parent epic (`Part of #<epic-number>`).
- **If slicing a raw idea (Case A)**:
  - Create the individual issues sequentially via `gh issue create`.
  - Link dependent issues (e.g. "Depends on #X").

### 4. Next Steps
- Output a clear summary with clickable links to all created GitHub issues.
- Recommend starting implementation on the first slice using `/refine <first-issue-number>`.
