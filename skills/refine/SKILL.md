---
name: refine
description: >-
  Refines a GitHub issue before implementation by analyzing the codebase,
  identifying architectural trade-offs, consulting the user for decisions,
  and updating the issue with concrete technical specs.
---

# Refine

Interactively clarify architecture, trade-offs, and specifications for a GitHub issue before writing code, giving the developer full control over technical decisions.

## Workflow

### 1. Context & Codebase Inspection
- Fetch the issue via `gh issue view <issue-number>`.
- Read repository rules (e.g., `AGENTS.md`, `PLAN.md`, architectural guidelines).
- Inspect related code, models, schemas, and endpoints to understand existing patterns and constraints.
- Verify existing tests and fixtures related to the feature or bug.

### 2. Identify Technical Fork Points
Before proposing solutions, analyze:
- **Architectural & Design Choices**: Alternative implementation approaches with clear pros and cons.
- **Data Model & Schema Impact**: Changes to tables, columns, constraints, migrations, or indexes (ensuring JIT schema evolution).
- **External Dependencies**: New libraries or APIs needed (checking exact versions and pinning rules).
- **Edge Cases & Failure Modes**: Network timeouts, provider rate limits, partial failures, deduplication, concurrency.
- **Cohesion & Slicing Viability**: Assess whether the issue contains multiple independent, separable capabilities. If it bundles multiple decoupled concerns that satisfy the 3 Independence Criteria (independent testability, zero cascading rework, autonomous reviewability), advise running `/slice <issue-number>` to decompose it. If it is a single cohesive capability (even if it touches models + API + tests together), **keep it unified** to avoid artificial coupling.

### 3. Developer Consultation & Decision Alignment
- Present key decisions to the developer clearly and concisely.
- For each open decision:
  - Explain the problem or trade-off briefly.
  - Provide concrete options (e.g., Option A vs. Option B) with trade-offs.
  - Recommend an option if appropriate, but wait for the developer's confirmation when the decision materially affects scope, architecture, or user-facing behavior and is not already settled by the request or repository rules. Resolve routine implementation details using existing conventions.
- Ask clarifying questions about user-facing behavior, error messages, or business rules.

### 4. Enrich the GitHub Issue
When this skill is invoked to refine an issue, updating that issue with the resulting specifications is part of the requested workflow. Once decisions are aligned with the developer, update the GitHub issue (using `gh issue edit <issue-number> --body-file <file>` or posting a detailed comment with `--body-file <file>`) using this structured format:

```markdown
## 📐 Technical Decisions & Architecture Plan

### Context & Scope
<Concise problem statement and confirmed scope boundaries>

### Confirmed Technical Decisions
- **Decision 1**: <What was decided and rationale>
- **Decision 2**: <What was decided and rationale>

### 🗄️ Schema & Data Model Changes
- <Tables, migrations, constraints, or 'None'>

### 🛠️ Implementation Plan
1. [`file-or-module`](path): <Specific change>
2. [`file-or-module`](path): <Specific change>

### 🧪 Test & Verification Strategy
- **Unit Tests**: <Specific edge cases and fixtures to test>
- **Integration Tests**: <Flows to test>
- **Command**: `make test` / `make lint`

### ✅ Acceptance Criteria
- [ ] <Specific criterion>
- [ ] <Specific criterion>
```

### 5. Ready for Implementation
- Confirm the issue is updated and ready.
- Suggest running `/implement <issue-number>` as the next step.
