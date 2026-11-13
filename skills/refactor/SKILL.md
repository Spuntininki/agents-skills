---
name: refactor
description: >-
  Surgically eliminates code smells and technical debt using Refactoring Guru
  techniques, strictly preserving observable behavior under characterization test safety.
---

# /refactor

Surgically eliminate code smells, pay down technical debt, and simplify design using **Refactoring Guru** techniques—with zero behavioral change and guaranteed test safety.

Rather than speculative or blanket rewrites, `/refactor` operates on-demand as a precision tool when a developer decides code requires structural cleanup.

## Guiding Principles

- **Behavior Invariant (The Zero Principle)**: Refactoring strictly modifies internal structure without changing observable behavior. Never fix bugs, change business rules, or add new features in a refactoring session. If a bug is discovered, isolate it with `/diagnose` or a separate fix.
- **Safety Net First (Characterization Harness)**: Never refactor code without automated test coverage. If existing tests are missing or shallow, write high-fidelity characterization tests *before* modifying production code to lock down invariants.
- **Surgical & Human-Scoped**: Only refactor what the developer requested or strictly identified in the target scope. Do not touch adjacent modules, format unrelated files, or rewrite whole architectures.
- **Prescriptive Recipes over Speculative Patterns**: Apply canonical Refactoring Guru transformation techniques (e.g. `Extract Method`, `Decompose Conditional`, `Introduce Parameter Object`) rather than introducing complex design patterns (Abstract Factory, Strategy, Decorator) unless polymorphism is explicitly required. Avoid over-engineering (YAGNI / KISS).
- **Atomic Micro-Steps & Continuous Verification**: Execute transformations in small, verifiable micro-steps. Run the test suite after every single transformation. If a step breaks tests or compilation, roll it back immediately before re-attempting.

---

## Workflow

### 1. Ingest Target Scope & Intent
Accept one or more inputs:
- Target file, method, or symbol:
  ```text
  /refactor src/services/order.ts:processPayment
  /refactor internal/domain/user.go
  ```
- Optional smell or specific transformation instruction:
  ```text
  /refactor src/services/order.ts:processPayment "eliminate Long Method and Data Clumps"
  /refactor pkg/billing/calculator.py "Replace Conditional with Polymorphism"
  ```
- If no instruction is provided, `/refactor` analyzes the target symbol for code smells and proposes a recipe before proceeding.

### 2. Establish Test Harness (Characterization Safety Net)
Before changing any production code:
1. **Locate Existing Tests**: Run tests covering the target symbol/file.
   - Verify all tests are passing.
2. **Coverage & Invariant Check**:
   - If tests are missing, brittle, or only test trivial paths: write **characterization tests** (*Michael Feathers / Working Effectively with Legacy Code*).
   - Characterization tests assert the *current actual behavior* (including edge cases, return values, and known quirks) to act as a regression lock.
   - Run tests and ensure they are 100% green.

### 3. Diagnose Code Smell & Select Canonical Recipe (Refactoring Guru)
Map the target issue to the canonical Refactoring Guru taxonomy and select the prescriptive remedy:

| Smell Family | Specific Code Smell | Primary Canonical Technique |
| :--- | :--- | :--- |
| **Bloaters** | **Long Method** | `Extract Method`, `Replace Temp with Query`, `Introduce Parameter Object` |
| | **Large Class** | `Extract Class`, `Extract Subclass`, `Extract Interface` |
| | **Primitive Obsession** | `Replace Data Value with Object`, `Introduce Parameter Object` |
| | **Data Clumps** | `Introduce Parameter Object`, `Preserve Whole Object` |
| | **Long Parameter List** | `Replace Parameter with Method Call`, `Introduce Parameter Object` |
| **OO Abusers** | **Switch Statements** | `Replace Conditional with Polymorphism`, `Replace Type Code with Subclasses/State` |
| | **Temporary Field** | `Extract Class`, `Introduce Null Object` |
| | **Refused Bequest** | `Replace Inheritance with Delegation`, `Extract Superclass` |
| **Change Preventers** | **Divergent Change** | `Extract Class` (single responsibility separation) |
| | **Shotgun Surgery** | `Move Method`, `Move Field`, `Inline Class` |
| **Dispensables** | **Duplicate Code** | `Extract Method`, `Pull Up Method`, `Form Template Method` |
| | **Dead Code** | `Remove Dead Code` (ruthlessly delete unused functions/types) |
| | **Speculative Generality** | `Collapse Hierarchy`, `Inline Class`, `Remove Parameter` |
| **Couplers** | **Feature Envy** | `Move Method`, `Extract Method` |
| | **Inappropriate Intimacy** | `Move Method`, `Move Field`, `Hide Delegate` |
| | **Message Chains** | `Hide Delegate`, `Extract Method` |
| | **Middle Man** | `Remove Middle Man`, `Inline Method` |

If the diagnosis is ambiguous or has multiple options, briefly present the proposed recipe to the developer:
> *"Target has **Long Method** (85 lines) and **Data Clumps** (address fields). Proposed plan: (1) Introduce `Address` parameter object, (2) Extract `validate_address` and `format_shipping_label`. Proceeding with atomic steps."*

### 4. Execute Atomic Micro-Steps
Refactor incrementally in micro-steps. Never apply a multi-phase refactoring in one edit:

```text
[Step N] Apply single transformation (e.g. Extract Method)
   ├── Edit code
   ├── Run compiler / linter
   ├── Run test suite (including characterization tests)
   └── If green: advance. If red: revert immediately.
```

#### Refactoring Rules of Engagement:
- **Preserve Public API**: Do not rename public exported methods or break call-sites unless explicitly requested. If renaming is necessary, use deprecation forwarding (keep old method delegating to new method).
- **No Inlined Feature Creep**: Do not "fix" a bug or "improve" business logic while refactoring. Log it separately.
- **No Speculative Abstractions**: Do not introduce generic factory layers or abstract base classes when a simple extracted helper function solves the smell.

### 5. Verification & Clean Reviewer Summary
1. Run full project test suite, linters, and type-checkers.
2. Verify zero regressions or contract breakage.
3. Present an executive summary formatted for human review:

```markdown
## 🧹 Refactoring Summary: `<symbol-or-file>`

- **Code Smell(s) Addressed**: `<e.g. Long Method, Data Clumps>`
- **Technique(s) Applied**: `<e.g. Extract Method, Introduce Parameter Object>`
- **Behavior Invariance**: 100% verified against existing & characterization tests.
- **Safety Net**: `<e.g. Added 3 characterization tests in tests/unit/test_order_char.py>`

### 🔍 Key Transformations
1. [`file#L10`](path): Extracted `<helper_function>` to simplify main logic flow.
2. [`file#L45`](path): Replaced primitive fields `(street, city, zip)` with `<Address>` value object.

### 🧪 Test Verification
- [x] Characterization tests passing.
- [x] Full test suite passing.
```
