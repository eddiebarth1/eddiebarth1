Produce a thorough, unambiguous implementation plan for a change that has already been vetted and agreed upon. The plan is not for ideation — the "what" is decided. The purpose here is to answer "how do we implement this safely and correctly?" in enough detail that a junior engineer with no prior knowledge of this codebase can execute it on the first attempt without guessing.

$ARGUMENTS — describe the vetted change. Include any agreed-upon constraints, scope, preferences, or context from the discussion that led to this decision.

## Context Bootstrap

Before planning anything, check whether `/deep-learn` has been run on this codebase:

```bash
cat .claude-learning-metadata.json 2>/dev/null
cat .claude-learning/synthesis.json 2>/dev/null
cat .claude-learning/codebase-indexer.json 2>/dev/null
cat .claude-learning/edge-failure-mapper.json 2>/dev/null
cat .claude-learning/test-fixtures-miner.json 2>/dev/null
```

**If synthesis.json exists**: This is your highest-value source. Use it as follows:
- **Tier 1 decisions** → inform the Constraints section: architectural choices that must not be violated
- **Tier 1 gotchas** → inform the Pitfalls section: these are real landmines, use them verbatim with evidence
- **Tier 1 conventions** → enforce in the Implementation Order: every step must follow documented conventions
- **Tier 2 risk map / failure modes** → inform the Risks and Tradeoffs section
- **Tier 2 test coverage** → inform the Testing section: highlight gaps the plan must fill
- **Tier 3 retrieval recipes** → execute fresh to find the exact files and line numbers to reference in the plan

**If codebase-indexer.json exists**: Use `modules` and `entry_points` to scope which files to read in Phase 1.

**If edge-failure-mapper.json exists**: Use `failure_modes` and `uncovered_edges` to surface risks the implementer must handle.

**If test-fixtures-miner.json exists**: Use `testing_infrastructure` to describe the exact testing patterns the new tests must follow.

**If no context exists**: Proceed with full discovery below. Consider running `/deep-learn` first — it will significantly reduce the risk of missing a critical constraint or pitfall.

---

## Phase 1: Deep Codebase Exploration

Do not write the plan until this phase is complete. Read broadly. Assumptions made without reading lead to incorrect plans.

1. **Identify every file that will be touched.** Read each one completely — no skimming. For each file, understand its role, its dependencies, and its invariants.

2. **Trace the full data flow** end-to-end: where does the relevant data enter the system? How is it transformed? Where is it persisted? How is it read back? How is it displayed or returned?

3. **Read every existing test** for the files you'll modify. Understand the testing infrastructure: what fixtures exist, how mocks are set up, what assertion patterns are used, what helpers are available.

4. **Read adjacent code** — files that import from, or are imported by, the affected files. Understand what contracts these files expose and what callers depend on.

5. **Search for existing patterns** for the type of change you're making:

```bash
# Find files that implement similar functionality
grep -rn "<key term from the change>" . | grep -v "node_modules\|vendor\|.git\|test"

# Find where the relevant data types are defined and used
grep -rn "<type name>" . | grep -v "node_modules\|vendor\|.git"
```

6. **Identify serialization and storage boundaries.** If the change touches models or data structures, trace where they're serialized/deserialized and verify what backward compatibility is required.

7. **Check the git history** on the files you'll modify — what has changed recently, and why?

```bash
git log --follow -p --stat -- <file> | head -100
```

---

## Phase 2: Constraints Inventory

Before writing a single implementation step, enumerate everything that must not break. Constraints are non-negotiable. If an implementation approach conflicts with a constraint, the approach is wrong — not the constraint.

For each constraint, answer:
- **What is it?** Name the invariant, contract, or critical behavior.
- **Where does it live?** File path and line numbers.
- **Why does it exist?** The reason this constraint was established (correctness, security, compliance, user trust, etc.)
- **How could this change violate it?** Specific, not vague — "this could break X if we do Y."

Common constraint categories to check:
- **Financial correctness**: any money/currency math that must be exact
- **Security invariants**: auth checks, input validation, access control gates
- **Data integrity**: unique constraints, referential integrity, consistency guarantees
- **API contracts**: public interfaces that callers depend on (changing them requires updating all callers)
- **Compliance**: legal, privacy, or platform requirements (GDPR, App Store rules, third-party ToS)
- **Concurrency safety**: shared state, race conditions, atomic operations
- **Backward compatibility**: stored data, exported formats, wire protocols

---

## Phase 3: Pitfall and Risk Analysis

Document every way this implementation could go wrong, and every tradeoff the implementer will need to be aware of.

**Pitfalls** — mistakes the implementer could make:
1. Type-level pitfalls (precision, null safety, coercion, enum serialization)
2. State management pitfalls (mutation vs immutability, async gaps, stale closures, mount checks)
3. Integration pitfalls (partial failure, rate limits, TOCTOU races, stale cache)
4. Testing pitfalls (testing implementation details, not testing behavior, missing edge-case coverage)
5. Known landmines in this codebase (surfaced from deep-learn or reading comments)

**Tradeoffs** — design decisions where there are legitimate alternatives:

| Decision | Option A | Option B | Chosen | Reasoning |
|----------|----------|----------|--------|-----------|
| ... | ... | ... | ... | ... |

Document the chosen approach and why. The plan must eliminate ambiguity — every design decision must be made here, not left to the implementer.

**Risks** — things that could go wrong after implementation:
- What could break in production that tests won't catch?
- What downstream systems or users could be affected?
- What is the rollback strategy if this needs to be reverted?

---

## Phase 4: Write the Plan

Structure the plan document as follows. Every section is required. Do not omit sections — if a section doesn't apply, write "N/A — [reason]" so the implementer knows it was considered.

---

### Section 1: Context

**The Problem**: What gap, bug, or need does this change address? Write it so someone who has never seen this project understands the "why."

**The Solution**: 3–5 sentences summarizing the approach. Define every term. No jargon without definition.

**Scope**: What is explicitly in scope? What is explicitly out of scope? A clear out-of-scope list prevents scope creep during implementation.

---

### Section 2: Glossary

Every domain-specific or codebase-specific term used in this plan must be defined here. If a term could be interpreted two ways, define the intended one. The implementer should never have to guess what a word means.

| Term | Definition |
|------|------------|
| ... | ... |

---

### Section 3: Constraints

List every non-negotiable invariant the implementation must preserve. For each:
- **Name**: Short identifier
- **Description**: What the constraint requires
- **Location**: File path / line numbers where it's enforced
- **Why it matters**: What breaks if violated
- **How this change could threaten it**: Specific, not vague

> **These are protected at all costs.** If any implementation step seems to conflict with a constraint, stop and resolve the conflict before proceeding.

---

### Section 4: Model / Data Changes

For every model, schema, or data structure change:
- **File path** and line numbers where the change goes
- **Exact field declarations** with types
- **`copyWith` / builder updates** using the pattern this codebase uses
- **Serialization updates**: both read and write paths
- **Backward compatibility**: what happens when existing data (pre-change) is loaded? Is a migration required?
- **Default values**: what does this field default to for existing records?

---

### Section 5: Core Logic Changes

For the main algorithm or business logic change:
- **Method signature** with full parameter documentation
- **Step-by-step algorithm** in pseudocode with concrete example values (e.g., "balance = $4,500, threshold = $1,000")
- **Reuse of existing helpers**: explicitly name which existing methods to call and which NOT to duplicate
- **Every design decision made explicitly**: when there's a choice, state the choice and the reasoning so the implementer doesn't re-litigate it

---

### Section 6: Tradeoffs and Risks

| Area | Tradeoff / Risk | Mitigation |
|------|----------------|------------|
| ... | ... | ... |

For each risk, state: what could go wrong, how likely it is, how bad it would be, and what the mitigation is. If no mitigation exists, say so — the implementer needs to know.

---

### Section 7: Edge Cases

| Edge Case | Input / Condition | Expected Behavior | How to Handle |
|-----------|-------------------|-------------------|---------------|
| ... | ... | ... | ... |

Be exhaustive. Include cases the implementer might think "that won't happen." It will.

---

### Section 8: UI / Screen Changes

For each visible change:
- **What the user sees**: describe the visual outcome precisely, or use an ASCII mockup
- **Which widget/component to modify**: file path and method/function name
- **What data feeds it**: which state fields, props, or store values drive this UI
- **Interaction behavior**: what happens on every user action (tap, swipe, submit, cancel, error)
- **Loading and error states**: what does the user see while waiting or when something fails?

If there are no UI changes, write "N/A — this is a backend/logic-only change."

---

### Section 9: Testing Requirements

Testing is not optional. Every change requires tests. "It works on my machine" is not a verification strategy.

For each test to write:
- **Test file path**: where the test lives (follow existing test file conventions)
- **Test group / describe block name**
- **Individual test names**: specific enough to understand what's being verified without reading the body
- **What each test verifies**: in plain English — behavior, not implementation
- **Setup required**: what fixtures, mocks, or state must be established
- **Key assertions**: the specific values, types, or invariants being checked
- **Edge cases that need their own tests**: don't hide multiple behaviors in one test

Required test coverage for this change:
- [ ] Happy path (normal input, expected output)
- [ ] Each constraint: a test that would catch a violation
- [ ] Each edge case from Section 7
- [ ] Failure paths: what happens when dependencies fail (DB, network, auth)
- [ ] Backward compatibility: if data format changed, a test that loads old data and verifies it still works

**What NOT to test**: scope out tests that aren't valuable so the implementer doesn't waste effort on them.

---

### Section 10: Files Modified Summary

| File | Action | What Changes |
|------|--------|--------------|
| ... | EDIT / NEW / DELETE | ... |

State "NO new files created" if applicable — this prevents file sprawl.

---

### Section 11: Implementation Order

A numbered sequence where **each step compiles (or lints clean) and passes all tests** before moving to the next. Do not group multiple risky changes into one step. The implementer should never be in a broken state.

| Step | Action | Verification |
|------|--------|--------------|
| 1 | ... | `<test/lint command>` passes |
| 2 | ... | `<specific test name>` passes |
| ... | ... | ... |

---

### Section 12: Verification Checklist

A concrete, runnable checklist. Each item must be specific enough to pass or fail — no vague items like "make sure it works."

**Automated:**
- [ ] Static analysis / linter clean (`<exact command>`)
- [ ] Full test suite passes (`<exact command>`)
- [ ] New tests pass
- [ ] No regressions in tests for adjacent code

**Manual:**
- [ ] `<Specific screen / endpoint>`: open it, do `<action>`, verify `<exact observable outcome>`
- [ ] Edge case: `<specific setup>`, verify `<exact result>`
- [ ] Error case: `<specific failure condition>`, verify `<error is handled gracefully>`

**Constraints:**
- [ ] `<Constraint name>`: verified by `<test name or manual step>`

---

### Section 13: Pitfalls to Watch For

A numbered list of the most dangerous mistakes the implementer could make. Each item must be:
- **Specific** — "use integer cents, never floats" not "be careful with numbers"
- **Actionable** — state exactly what TO do, not just what to avoid
- **Contextual** — explain WHY this pitfall exists in this codebase

---

## Phase 5: Self-Review Gate

Before delivering the plan, verify:

1. **Read it as the implementer.** Is there any step where you'd need to ask a question? If yes, answer it in the plan.
2. **Check for implicit knowledge.** Did you assume the reader knows something about this codebase? Make it explicit.
3. **Verify the implementation order.** Does each step truly compile independently? Are there hidden dependencies between steps?
4. **Count the files.** Does the Section 10 summary table match every file mentioned anywhere in the plan?
5. **Check the edge cases.** For each edge case, is the "how to handle" specific enough to implement without guessing?
6. **Check the constraints.** Is there a test or verification step for every constraint listed in Section 3?
7. **Check the tradeoffs.** Is every design decision made — or is the implementer being asked to make a call that should have been made here?

If any check fails, fix the plan before delivering it.

---

## Output

Write the plan to a `<DESCRIPTIVE_NAME>_PLAN.md` file in the project root. Suggest a name based on the feature (e.g., `OFFLINE_SYNC_PLAN.md`, `PAYMENT_RETRY_PLAN.md`). Also provide a brief summary in the conversation of what the plan covers and any high-priority concerns surfaced during planning.

## Quality Bar

The plan meets the bar when:
- A developer who has **never seen this codebase** could implement it step-by-step without asking a single question
- Every design decision is **made in the plan** — zero decisions are left to the implementer
- Every file path, method name, and type name is **exact** — no "somewhere in the models folder"
- The constraints section would **catch a violation** during implementation, not after
- The testing section would produce a test suite that **actually catches regressions**
- The pitfalls section would prevent the **most common mistakes** a junior engineer would make on this specific codebase
