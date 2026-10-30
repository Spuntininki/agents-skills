---
name: slice
description: >-
  Breaks down a feature idea or large GitHub issue into small, vertically sliced
  micro-issues (≤ 200-300 lines of diff budget each) organized in an
  orchestrator-ready dependency graph targeting an Epic Integration Branch.
---

# /slice

Break down complex feature ideas or large GitHub issues into small, independent, vertically sliced micro-issues with strict diff budgets (≤ 200–300 lines of code change per issue). 

Organizes child issues under a parent Tracking Issue (Epic) with an explicit execution order and an **Epic Integration Branch**, designed for both human review and automated orchestrator-subagent workflows.

## Guiding Principles

- **Independently Testable**: Every slice MUST be testable on its own upon implementation. Its scope must be self-contained enough that unit or integration tests prove the new behavior works without requiring unmerged future slices. Never leave untestable or dead-end ghost code.
- **Single Cohesive Concern**: Each issue addresses exactly one capability, behavior, or architectural step. Focus on doing one thing completely rather than multiple unrelated things halfway.
- **Diff Budget as a Sizing Guide (≤ 200–300 lines)**: Aim for small, reviewable diffs to keep PR reviews fast and fatigue-free. Do not impose arbitrary file-count limits (a cohesive change touching models, schemas, routers, and tests is completely natural).
- **Strict Scope Delimitation**: Every slice must explicitly state what is IN scope and what is OUT of scope (deferred to subsequent slices) to prevent scope creep during implementation.
- **Epic Integration Branch (Single Atomic Deployment)**:
  - Micro-PRs merge into a parent integration branch (`epic/issue-<epic-number>-<slug>`), NOT directly into `main`.
  - Prevents deploying 4 incomplete partial versions to production / VPS.
  - Slices are reviewed individually against the epic branch; once all slices are complete, a single final PR merges the epic into `main`, triggering one clean, atomic CD build and rollout.
- **Orchestrator-Ready Execution Graph**: Slices must have an explicit sequential order (`Order: 1 of N`, `2 of N`, etc.) and clear blocking dependencies (`Depends on: #X` or `None`). This allows an orchestrator agent to dispatch subagents sequentially without context collision.
- **Parent Tracking Issue (Epic as State Machine)**: The parent issue acts as the central coordinator and state machine. It maintains a numbered task checklist with direct links to child issues (`- [ ] 1. #X ...`). As child PRs merge, the checklist updates, advancing the orchestrator.

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

### 2. Propose Vertical Slices & Execution Order
Before creating issues on GitHub, present the proposed breakdown to the developer:
- Explain why the task should be divided (multi-layer impact, diff budget exceedance).
- Present 2 to 4 vertical slices, ordered by dependency:
  - **Slice 1 [Order: 1 of N | Depends on: None]**: Foundation/Core (e.g. Data models, migrations, domain services, unit tests).
  - **Slice 2 [Order: 2 of N | Depends on: Slice 1]**: Transport/Service (e.g. API endpoints, workers, integration tests).
  - **Slice 3 [Order: 3 of N | Depends on: Slice 2]**: Consumer/Presentation (e.g. Web UI, bot commands, generated SDK client).
- For each slice, define:
  - Conventional commit title (`type(scope): imperative summary`).
  - Clear scope boundaries: **What is IN scope** vs. **What is explicitly OUT of scope** (deferred to next slice).
  - Concrete acceptance criteria (checkboxes).
- Announce the target integration branch: `epic/issue-<epic-number>-<slug>`.
- Ask for the developer's confirmation or adjustments.

### 3. Create / Update GitHub Issues
Once confirmed by the developer:

#### If slicing an existing issue (Case B):
1. Create child issues sequentially via `gh issue create`:
   - Title: Conventional commit format (`feat(...)`, `fix(...)`).
   - Labels: matching repo labels (`enhancement`, `bug`).
   - Body structure:
     ```markdown
     ## 🎯 Context
     Part of Epic #<parent-number>
     - **Integration Branch**: `epic/issue-<parent-number>-<slug>` (PR Base)
     - **Execution Order**: <k> of <N>
     - **Dependencies**: #<previous-issue> (must be merged into epic branch first) <!-- or "None" -->

     ## 📦 Scope
     - **IN Scope**: <Specific cohesive capability delivered>
     - **OUT of Scope**: <Explicitly deferred to subsequent slices>

     ## 🧪 Verification & Acceptance Criteria
     - [ ] Unit / Integration tests pass verifying this slice independently.
     - [ ] <Concrete acceptance criterion 1>
     - [ ] <Concrete acceptance criterion 2>
     ```
2. Convert the parent issue into a **Tracking Issue (Epic)** using `gh issue edit <parent-number> --body ...`:
   - Add the sequential execution checklist with links to created child issues:
     ```markdown
     ## 🌿 Integration Branch
     `epic/issue-<parent-number>-<slug>` (Child PRs target this branch. Merged to `main` only when all slices complete).

     ## 🗺️ Execution Plan & Progress
     - [ ] 1. #<child-1> `<title>` (Dependencies: None)
     - [ ] 2. #<child-2> `<title>` (Depends on #<child-1>)
     - [ ] 3. #<child-3> `<title>` (Depends on #<child-2>)
     ```

#### If slicing a raw idea (Case A):
1. Create the parent Epic issue first via `gh issue create --title "feat(scope): <epic-title>" ...`.
2. Follow the steps above to create the child issues and update the parent Epic with the execution checklist.

### 4. Next Steps
- Output a clear summary with clickable links to all created GitHub issues.
- Recommend starting orchestrator execution:
  - Run `/orchestrate <parent-epic-number>` to supervise the workflow end-to-end.
