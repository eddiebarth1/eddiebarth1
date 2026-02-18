Perform a thorough, context-aware review of a pull request or set of changes. Unlike a surface-level diff review, this goes deep: check correctness, security, performance, test coverage, architectural fit, and consistency with the patterns of this specific codebase.

## Setup

If a PR number or branch name is provided as an argument, fetch the diff. Otherwise, review staged/unstaged changes:

```bash
# If argument is a PR number:
gh pr view $ARGUMENTS --json title,body,author,additions,deletions,changedFiles
gh pr diff $ARGUMENTS

# If argument is a branch name:
git diff main...$ARGUMENTS

# If no argument (review current working changes):
git diff HEAD
git diff --staged
```

Read the PR description/commit message to understand the intent of the change.

## Phase 1: Change Scope Assessment

1. How many files changed? How many lines?
2. What is the stated purpose of this change?
3. Is the scope appropriate? (Does this PR do one thing, or is it trying to do many?)
4. Are there any files in the diff that seem unrelated to the stated purpose?

## Phase 2: Correctness Review

Read every changed file completely. For each change, ask:

1. **Does it do what it claims?** Verify the implementation matches the description
2. **Edge cases**: What happens with empty inputs, zero values, null/nil, very large inputs, concurrent access?
3. **Error handling**: Are all error paths handled? Are errors propagated correctly or swallowed?
4. **State consistency**: If the change modifies state, are all state transitions valid?
5. **Race conditions**: For concurrent code, are there potential race conditions or deadlocks?
6. **Off-by-one errors**: Check all loops, slice indices, and pagination logic
7. **Logic errors**: Walk through the logic manually for at least one representative case

## Phase 3: Security Review

Apply the same checks as `/security-scan` but focused on the changed code:

1. Is any user input used without validation or sanitization?
2. Are there new SQL queries? Are they parameterized?
3. Are there new shell executions? Is the input safe?
4. Are there new file operations? Is path traversal prevented?
5. Are new endpoints protected with appropriate authentication/authorization?
6. Are secrets or credentials introduced anywhere?
7. Are new dependencies introduced? Do they have known vulnerabilities?

## Phase 4: Performance Review

1. Are there new database queries? Could they cause N+1 problems?
2. Are there new loops over collections? What's the complexity?
3. Are there new network calls? Are they appropriately parallelized or cached?
4. Are there new allocations or data copies that could be avoided?
5. Is the change on a hot path? What's the performance impact?

## Phase 5: Test Coverage Review

```bash
# Show test files in the diff
git diff HEAD --name-only 2>/dev/null | grep -E "test|spec"
gh pr diff $ARGUMENTS 2>/dev/null | grep "^+" | grep -E "test|spec|assert|expect"
```

1. Are there tests for the new functionality?
2. Do the tests cover the happy path AND error paths?
3. Do the tests cover the edge cases identified in Phase 2?
4. Are the tests meaningful or just written for coverage?
5. Are any existing tests being deleted or weakened?

## Phase 6: Consistency Review

Compare the changes against the patterns established in this codebase:

1. **Naming**: Do new names follow the conventions of this codebase?
2. **Error handling**: Does it handle errors the way this codebase handles errors?
3. **Code organization**: Is new code in the right layer/file/module?
4. **Abstraction level**: Is the new code at a consistent abstraction level with its neighbors?
5. **Documentation**: Are new public APIs documented the way other public APIs are?
6. **Test style**: Are new tests written in the style of existing tests?

## Phase 7: Architectural Review

1. Does this change fit the existing architecture or does it introduce a new pattern that isn't justified?
2. Does this create new coupling between modules that should be independent?
3. Does this change an interface or contract that other code depends on? Are callers updated?
4. Does this introduce a dependency that should be injected instead of hard-coded?
5. Is this the right place to add this logic, or does it belong in a different layer?

## Phase 8: Synthesis

Produce a structured review:

**Summary**: One paragraph on what this PR does and your overall assessment.

**Must Fix** (blocking):
- Issues that must be resolved before merging (correctness bugs, security issues, missing tests for critical paths)

**Should Fix** (non-blocking but important):
- Issues that should be addressed soon (performance concerns, architectural decisions that will cause problems later)

**Nits** (optional):
- Style inconsistencies, minor improvements, suggestions

**What's Good**:
- Highlight well-done parts of the implementation

**Questions**:
- Things where you need more context from the author

**Test Coverage Assessment**: What's covered and what gaps exist.

**Overall Verdict**: Approve / Request Changes / Needs Discussion

$ARGUMENTS
