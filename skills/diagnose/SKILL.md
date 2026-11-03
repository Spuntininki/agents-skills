---
name: diagnose
description: >-
  Investigates bug reports, errors, and failing tests using an isolated subagent for
  root cause analysis (RCA), creates GitHub bug issue(s), and registers them into an Epic
  for /orchestrate or /implement.
---

# /diagnose

Investigate bugs, incidents, or failing tests with rigorous **Root Cause Analysis (RCA)** and convert findings into actionable, epic-integrated GitHub issues.

## Guiding Principles

- **Context Isolation via Subagent**: Deep forensic investigations (parsing stack traces, grepping logs, running `git blame`/`git log -S`, testing reproduction scripts) quickly pollute context. Delegating investigation to an isolated research subagent keeps the orchestrating agent clean and decisive.
- **Root Cause vs. Symptom**: Never treat the immediate error (e.g. `NullPointerException`, `IndexOutOfBounds`, HTTP 500) as the bug. Trace backward to the broken invariant, unhandled edge condition, race condition, or schema drift.
- **Reproduction First**: A bug without reproduction is guesswork. Isolate minimal reproduction steps or a failing test case before formulating any fix.
- **Decoupled Issues for Multiple Bugs**: If an incident or failure trace stems from multiple distinct failures (e.g. invalid payload accepted at ingress + unhandled retry explosion in worker queue), break them into independent, modular bug issues.
- **Epic-Ready Integration**: Seamlessly register newly created bug issues into an Epic's checklist with execution modes (`Parallel ⚡` vs `Serial 🔒`) and dependencies, preparing them for immediate execution via `/orchestrate`.

---

## Workflow

### 1. Ingest Problem Input
Accept one or more of:
- Error log or stack trace.
- Bug report or user incident summary.
- Link to failing CI run, test, or existing raw issue.
- Optional flag/parameter: `--epic <epic-number-or-url>` (to associate the bug with an active Epic).

### 2. Dispatch Forensic RCA Subagent
Invoke an isolated research/investigation subagent:
```text
Task: Perform Root Cause Analysis on the reported issue:
"<input>"

1. Trace execution flow through the codebase from the failure point backward.
2. Check recent git history in affected modules (`git log -S`, `git blame`) to identify regressions.
3. Distinguish root cause (broken invariant, race condition, state corruption) from symptoms.
4. Formulate minimal reproduction steps or a reproduction test script.
5. Identify blast radius and affected files.
6. If multiple decoupled bugs caused this incident, isolate each one separately.

Return a structured RCA report.
```

### 3. Review & Synthesize RCA Findings
Evaluate the subagent's RCA report:
- **Observed Symptom**: Surface failure, HTTP status, or crash.
- **Root Cause**: The underlying flaw (missing constraint, race condition, contract mismatch).
- **Reproduction**: Minimal test command or script demonstrating the failure.
- **Blast Radius & Affected Files**: Specific files and dependencies affected.
- **Execution Mode**:
  - `Parallel ⚡`: Independent bug(s) that can be fixed concurrently in separate worktrees without shared state.
  - `Serial 🔒`: Dependent bug(s) requiring a specific order of execution.

### 4. Create GitHub Bug Issue(s)
For each distinct bug, inherit the parent Epic's milestone (if `--epic` was provided) and create the issue:
```bash
MILESTONE=""
if [ -n "<epic-id>" ]; then
  MILESTONE=$(gh issue view <epic-id> --json milestone -q .milestone.title 2>/dev/null || echo "")
fi

gh issue create \
  --title "fix: <concise, descriptive bug title>" \
  --label "bug" \
  ${MILESTONE:+-m "$MILESTONE"} \
  --body "$(cat << 'EOF'
## 🎯 Observed Symptom
<What happens, error logs, or failing test output>

## 🔍 Root Cause Analysis (RCA)
<Why it happened: broken invariant, race condition, edge case, or schema drift>

## 🧪 Reproduction
```bash
<Minimal command, curl, or test run reproducing the failure>
```

## 🛠️ Proposed Fix & Blast Radius
- **Target Files**: [`path/to/file.ext`](path/to/file.ext#L10-L40)
- **Fix Strategy**: <Concise explanation of the fix without premature micro-implementation>
- **Blast Radius**: <Potential side-effects, downstream consumers, or migrations>

## ✅ Definition of Done / Acceptance Criteria
- [ ] Reproduction test passes.
- [ ] No regression in related suites.
- [ ] Verified under edge cases.
EOF
)"
```

### 5. Epic Registration (Prepare for /orchestrate)
- **If `--epic <epic-id>` was provided or an Epic is active**:
  - Append the newly created issue(s) to the Epic's checklist via `gh issue edit`:
    ```markdown
    - [ ] Fix <short-description> #<bug-issue-id> (Mode: Parallel ⚡ | Serial 🔒, Deps: <none|#dep>)
    ```
- **If no Epic exists and multiple bugs were created**:
  - Offer to create a tracking Bugfix Epic:
    ```bash
    gh issue create \
      --title "epic: resolve <incident-name-or-cluster>" \
      --label "epic" \
      --body "<Checklist with all diagnosed bug issues>"
    ```

### 6. Next Step
Confirm issue creation and provide the next command:
- **Single Bug**: Recommend `Run /implement <bug-issue-id>`.
- **Epic / Multi-Bug**: Recommend `Run /orchestrate <epic-id>` to dispatch concurrent worktrees for parallel fixes or sequence serial fixes.
