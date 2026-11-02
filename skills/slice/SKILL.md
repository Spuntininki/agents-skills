---
name: slice
description: >-
  Breaks down a feature idea or large GitHub issue into independent, vertically sliced
  micro-issues with explicit execution modes (Parallel vs. Serial) organized in an
  orchestrator-ready dependency graph targeting an Epic Integration Branch.
---

# /slice

Break down complex feature ideas or large GitHub issues into independent, vertically sliced micro-issues targeting an **Epic Integration Branch**.

Prioritizes functional independence, cohesive capabilities, and execution efficiency (tagging slices as **Parallel ⚡** or **Serial 🔒** for subagent dispatch), avoiding arbitrary line-count limits and anti-pattern horizontal layer slicing.

## Guiding Principles

- **Cohesion First (Anti-Cascading Coupling)**: Never slice a task along arbitrary line limits or horizontal technical layers (e.g., DB in one issue, API in another). Slices touching models, routes, domain logic, and tests together for a single cohesive capability are natural and healthy. If changing Slice B requires rewriting or reopening Slice A, **they belong to the same issue**.
- **The 3 Independence Criteria (Slice Gate)**: Slicing is ONLY permitted when every resulting child issue satisfies:
  1. *Change Independence (Zero Cascade)*: Upstream slices remain valid and closed even if downstream slices are modified or deferred.
  2. *Closed Testability (Zero Ghost Code)*: The slice delivers real, runnable unit/integration tests proving working behavior without depending on unmerged future slices.
  3. *Autonomous Reviewability*: A reviewer can fully understand, verify, and approve the PR without opening a second PR or holding unmerged mental context.
- **Execution Mode (Parallel ⚡ vs. Serial 🔒)**:
  - **Parallel ⚡**: For slices that can be implemented concurrently by subagents in isolated worktrees (e.g., different adapters, endpoints, or independent consumers). Slices in the same parallel phase must have **disjoint file boundaries** to guarantee zero merge friction.
  - **Serial 🔒**: For foundational steps that establish base schemas/contracts needed by others, or final integration wiring steps that depend on multiple upstream slices.
- **Disjoint File Boundaries for Parallel Slices**: Slices flagged as `Parallel` MUST touch distinct directories or files. If two tasks must edit the exact same shared file (e.g. route registrations), extract the shared structure into an upstream foundation slice or keep them sequential.
- **Epic Integration Branch (Single Atomic Deployment)**:
  - Micro-PRs merge into a parent integration branch (`epic/issue-<epic-number>-<slug>`), NOT directly into `main`.
  - Prevents deploying incomplete partial versions to production / VPS.
  - Slices are reviewed individually against the epic branch; once all slices are complete, a single final PR merges the epic into `main`, triggering one clean, atomic CD build and rollout.
- **Parent Tracking Issue (Epic as State Machine)**: The parent issue acts as the central coordinator and state machine. It organizes tasks by execution phases with explicit parallel/serial execution modes (`- [ ] 2A. #X (Mode: Parallel | Depends on: #Y)`).

## Workflow

### 1. Input Analysis & Slicing Viability
Determine the input type:
- **Case A: Raw Feature Idea / Prompt** (e.g. `/slice Add notification preferences and multiple delivery channels`):
  - Inspect codebase architecture, models, schemas, and directory structure.
  - Assess whether the feature contains multiple **independent capabilities**.
- **Case B: Existing GitHub Issue** (e.g. `/slice 18` or `/slice https://github.com/.../issues/18`):
  - Fetch issue details via `gh issue view <issue-number>`.
  - Check whether the issue is a single atomic capability or an aggregate of separable concerns.

> [!IMPORTANT]
> **Anti-Slicing Check**: If the task is a single atomic algorithm, invariant, or cohesive flow (even if dense or spanning DB + API), **do not slice it**. Recommend keeping it as a single issue. Only slice if genuine functional independence exists.

### 2. Propose Vertical Slices & Execution Graph (Phases)
Before creating issues on GitHub, present the proposed breakdown to the developer:
- Explain why slicing is beneficial for this specific feature (decoupled capabilities, opportunities for parallel implementation).
- Organize the breakdown into **Phases / Stages**:
  - **Phase 1: Foundation (Serial 🔒)**: Shared contracts, base domain models, or migrations (Dependencies: None).
  - **Phase 2: Independent Implementations (Parallel ⚡)**: Independent adapters, processors, or features running concurrently in separate worktrees with disjoint file boundaries.
  - **Phase 3: Integration & Wiring (Serial 🔒)**: Router wiring, end-to-end integration tests, or UI aggregation (Depends on Phase 2).
- For each slice, define:
  - Title in Conventional Commit format (`type(scope): imperative summary`).
  - **Execution Mode**: `Parallel ⚡` or `Serial 🔒`.
  - **Dependencies**: `#<previous-issue>` or `None`.
  - **Target File Boundaries**: Explicit paths touched to guarantee zero overlap for parallel tasks.
  - Clear scope boundaries: **What is IN scope** vs. **What is explicitly OUT of scope**.
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
     - **Execution Mode**: ⚡ `Parallel` <!-- or 🔒 `Serial` -->
     - **Dependencies**: #<previous-issue> <!-- or "None" -->
     - **File Boundaries**: `<specific/path/1/*>`, `<specific/path/2/*>`

     ## 📦 Scope
     - **IN Scope**: <Specific cohesive capability delivered>
     - **OUT of Scope**: <Explicitly deferred to subsequent slices>

     ## 🧪 Verification & Acceptance Criteria
     - [ ] Unit / Integration tests pass verifying this slice independently.
     - [ ] <Concrete acceptance criterion 1>
     - [ ] <Concrete acceptance criterion 2>
     ```

2. Convert the parent issue into a **Tracking Issue (Epic)** using `gh issue edit <parent-number> --body ...`:
   - Add the phase-based execution checklist with links to created child issues and execution modes:
     ```markdown
     ## 🌿 Integration Branch
     `epic/issue-<parent-number>-<slug>` (Child PRs target this branch. Merged to `main` only when all slices complete).

     ## 🗺️ Execution Plan & Progress

     ### Phase 1: Foundation (Serial 🔒)
     - [ ] 1. #<child-1> `<title>` (Mode: Serial | Depends on: None)

     ### Phase 2: Independent Capabilities (Parallel ⚡)
     - [ ] 2A. #<child-2> `<title>` (Mode: Parallel | Depends on: #<child-1>)
     - [ ] 2B. #<child-3> `<title>` (Mode: Parallel | Depends on: #<child-1>)

     ### Phase 3: Integration & Polish (Serial 🔒)
     - [ ] 3. #<child-4> `<title>` (Mode: Serial | Depends on: #<child-2>, #<child-3>)
     ```

#### If slicing a raw idea (Case A):
1. Create the parent Epic issue first via `gh issue create --title "feat(scope): <epic-title>" ...`.
2. Follow the steps above to create child issues and update the parent Epic with the execution checklist.

### 4. Next Steps
- Output a clear summary with clickable links to all created GitHub issues.
- Highlight which issues can be started immediately (and in parallel).
- Recommend starting orchestrator execution:
  - Run `/orchestrate <parent-epic-number>` to supervise the workflow end-to-end.
