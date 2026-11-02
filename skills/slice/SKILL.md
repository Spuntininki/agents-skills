---
name: slice
description: >-
  Breaks down a feature idea or large GitHub issue into independent, vertically sliced
  micro-issues with parallel/serial execution modes targeting an Epic Integration Branch.
---

# /slice

Decompose features or large issues into independent, vertically sliced micro-issues targeting an **Epic Integration Branch** (`epic/issue-<epic>-<slug>`).

## Core Rules

1. **Cohesion First (Anti-Cascading Coupling)**: Never slice along arbitrary line limits or horizontal layers (e.g. DB in one issue, API in another). Slices spanning models, routes, and tests together for a single cohesive capability are natural. If modifying Slice B requires altering Slice A, **they belong to the same issue**.
2. **Low Cognitive Load Review (~15 min)**: Each PR must be quick and cheap for a human to review (~15 minutes of focused reading). If a feature is too dense, split along natural behavioral seams (e.g. happy path first, complex retries/edge cases second), never by technical layers.
3. **Execution Modes**:
   - `⚡ Parallel`: Independent tasks with **disjoint file boundaries** (zero merge conflicts). Run concurrently in separate worktrees.
   - `🔒 Serial`: Foundational schemas/contracts, or final wiring steps with blocking dependencies.

## Workflow

1. **Analysis & Viability**:
   - Inspect codebase architecture, models, and tests.
   - **Anti-Slicing Check**: If the task is a single atomic capability or invariant, **do not slice it**. Only slice if multiple decoupled capabilities exist.

2. **Propose Execution Graph**:
   - Group proposed slices into **Phases** (Phase 1: Foundation 🔒, Phase 2: Independent Features ⚡, Phase 3: Wiring 🔒).
   - Specify: Title (`type(scope): summary`), Mode (`Parallel ⚡` vs `Serial 🔒`), Dependencies (`#prev` or `None`), Target File Boundaries, Scope (IN/OUT), and Acceptance Criteria.
   - Confirm breakdown with developer before creating issues.

3. **Create Issues**:
   - If parent Epic issue does not exist, create it: `gh issue create --title "feat(scope): <title>" ...`.
   - Create child issues with `gh issue create`:
     ```markdown
     ## 🎯 Context
     Part of Epic #<parent-number>
     - **Integration Branch**: `epic/issue-<parent-number>-<slug>`
     - **Execution Mode**: ⚡ `Parallel` <!-- or 🔒 `Serial` -->
     - **Dependencies**: #<previous> <!-- or "None" -->
     - **File Boundaries**: `<paths-touched>`

     ## 📦 Scope
     - **IN Scope**: <Cohesive capability>
     - **OUT of Scope**: <Deferred items>

     ## 🧪 Verification & Acceptance Criteria
     - [ ] Unit / Integration tests pass verifying this slice independently.
     - [ ] <Concrete criterion>
     ```
   - Update parent Epic body with the phase checklist:
     ```markdown
     ## 🌿 Integration Branch
     `epic/issue-<parent-number>-<slug>`

     ## 🗺️ Execution Plan & Progress
     ### Phase 1: Foundation (Serial 🔒)
     - [ ] 1. #<id> `<title>` (Mode: Serial | Depends on: None)

     ### Phase 2: Independent Implementations (Parallel ⚡)
     - [ ] 2A. #<id> `<title>` (Mode: Parallel | Depends on: #<prev>)
     - [ ] 2B. #<id> `<title>` (Mode: Parallel | Depends on: #<prev>)

     ### Phase 3: Wiring (Serial 🔒)
     - [ ] 3. #<id> `<title>` (Mode: Serial | Depends on: #2A, #2B)
     ```

4. **Next Steps**: Link created issues and recommend `/orchestrate <parent-number>`.
