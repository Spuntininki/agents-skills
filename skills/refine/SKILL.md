---
name: refine
description: >-
  Refines a GitHub issue or multi-issue Epic before implementation by analyzing the codebase,
  aligning cross-cutting architectural trade-offs, consulting the user for decisions,
  and enriching issues with technical specs.
---

# /refine

Clarify architecture, trade-offs, and technical specs for an issue or an entire Epic before writing code.

## Invocation
```text
/refine <issue-or-epic-number>
```
- `<issue-or-epic-number>`: Issue number or URL of a standalone issue or a parent Epic.

## Workflow

1. **Target Detection & Scope Analysis**:
   - Inspect target:
     ```bash
     gh issue view <number> --json title,body,milestone
     ```
   - **Epic Check**: Check if the issue represents an Epic (contains a checklist of child issues `- [ ] #<child-id>` or Phase breakdown).
     - If **Epic**, execute **Path A: Epic-Wide Refinement**.
     - If **Single Issue**, execute **Path B: Single-Issue Refinement**.

---

### Path A: Epic-Wide Refinement (Multi-Issue Epic)

1. **Extract Child Issues & Map Dependencies**:
   - Parse all child issue numbers from the checklist/body.
   - Fetch each child issue: `gh issue view <child-id> --json title,body`.
   - Identify execution modes (`Parallel ⚡` vs `Serial 🔒`) and file boundaries.

2. **Global & Cross-Cutting Architectural Scan**:
   - Analyze shared systems across all slices: data models/migrations, API payloads/contracts, authentication, error handling conventions, and external dependencies.
   - **Anti-Collision Guard**: Detect fork points where concurrent subagents in worktrees could make incompatible architectural decisions or lock shared resources.

3. **Developer Consultation (Two-Tier Q&A)**:
   - **Tier 1 (Global Decisions)**: Present cross-cutting decisions affecting multiple slices (Option A vs Option B with trade-offs and recommendation). Wait for user confirmation.
   - **Tier 2 (Per-Slice Ambiguities)**: For slices with open questions, business rule uncertainties, or edge cases, present specific fork points. (Skip slices that are already deterministic).

4. **Enrich Epic & Child Specifications (Comment-First)**:
   - **Parent Epic Comment**: Post confirmed Global Architecture Plan:
     ```bash
     gh issue comment <epic-number> --body "..."
     ```
     ```markdown
     ## 🏛️ Global Architecture Decisions & Conventions
     - **Confirmed Global Trade-offs**: <Decisions agreed upon and rationale>
     - **Shared Contracts & Conventions**: <Schemas, DTO formats, error handling standards>
     - **Pre-requisites & Shared Fixtures**: <Shared migrations or baseline modules>
     ```
   - **Child Issues Comments**: Comment on each child issue with its specific technical specification and agreed contracts:
     ```bash
     gh issue comment <child-id> --body "..."
     ```
     ```markdown
     ## 📐 Technical Specification & Implementation Plan
     - **Confirmed Architecture**: <Specific patterns & agreed shared conventions>
     - **Files to Modify / Create**: [`path`](path)
     - **Test Strategy & Edge Cases**: <Concrete verification criteria>
     ```

5. **Next Step**: Confirm readiness and recommend `/orchestrate <epic-number>`.

---

### Path B: Single-Issue Refinement (Standalone Issue)

1. **Inspection & Slicing Viability**:
   - Inspect related code, models, and tests.
   - **Cohesion Check**: If the issue bundles multiple independent capabilities that can be separately developed and tested, advise running `/slice <issue-number>`. If it is a single cohesive capability, keep it unified.

2. **Map Technical Fork Points**:
   - Identify concrete trade-offs: architectural patterns, schema changes, failure modes, concurrency, and performance.

3. **Developer Consultation**:
   - Present open decisions with concrete options (Option A vs Option B) and trade-offs. Recommend an option and wait for developer confirmation.

4. **Enrich Issue Specification (Comment-First)**:
   - Post specification comment (`gh issue comment <issue-number> --body ...`):
     ```markdown
     ## 📐 Technical Decisions & Architecture Plan
     - **Confirmed Decisions**: <What was decided and rationale>
     - **Schema / Data Changes**: <Migrations, tables, or 'None'>

     ### 🛠️ Implementation Plan
     1. [`file-or-module`](path): <Specific change>

     ### 🧪 Test Strategy & Acceptance Criteria
     - **Tests**: <Edge cases and integration flows>
     - [ ] <Concrete acceptance criterion 1>
     - [ ] <Concrete acceptance criterion 2>
     ```

5. **Next Step**: Confirm readiness and recommend `/implement <issue-number>`.
