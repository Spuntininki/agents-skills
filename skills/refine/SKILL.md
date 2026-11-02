---
name: refine
description: >-
  Refines a GitHub issue before implementation by analyzing the codebase,
  identifying architectural trade-offs, consulting the user for decisions,
  and updating the issue with technical specs.
---

# /refine

Clarify architecture, trade-offs, and technical specs for an issue before writing code.

## Workflow

1. **Inspection & Slicing Viability**:
   - Fetch issue: `gh issue view <issue-number>`. Inspect related code, models, and existing tests.
   - **Cohesion Check**: If the issue bundles multiple independent capabilities that can be separately developed and tested, advise running `/slice <issue-number>`. If it is a single cohesive capability (even spanning models + API + tests), keep it unified.

2. **Map Technical Fork Points**:
   - Identify concrete trade-offs: architectural patterns, schema/migration changes, external dependencies, failure modes, and concurrency concerns.

3. **Developer Consultation**:
   - Present open decisions with concrete options (Option A vs Option B) and trade-offs. Recommend an option and wait for developer confirmation on architectural or scope decisions.

4. **Enrich Issue Specification**:
   - Update issue body (`gh issue edit <issue-number> --body ...` or comment) with confirmed specs:
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
