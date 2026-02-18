Extract and document the coding patterns, conventions, and implicit standards of this codebase. The goal is to produce a living style guide derived entirely from what already exists - not what a linter enforces, but what the team actually does. This is essential for writing code that looks like it belongs here.

## Phase 1: Naming Conventions

Analyze naming across the codebase:

```bash
# Sample function/method names
grep -rn --include="*.js" --include="*.ts" --include="*.go" --include="*.py" \
  -E "^(function |def |func |const |let |var |class )" . \
  | grep -v "node_modules\|vendor\|test\|spec" | head -80
```

From this, determine:
1. **Variables**: camelCase, snake_case, SCREAMING_SNAKE for constants?
2. **Functions/Methods**: verb-first (getUserById) vs noun-first (userById)?
3. **Classes/Types**: PascalCase? Suffixes (Service, Manager, Handler, Repository, etc.)?
4. **Files**: kebab-case, snake_case, camelCase? How do they map to the thing they contain?
5. **Test files**: Where do they live? What suffix (.test.js, _test.go, spec.rb)?
6. **Boolean variables**: Is-prefixed (isActive, hasPermission) or not?

## Phase 2: Error Handling Patterns

Find how errors are handled throughout the codebase:

```bash
# Error handling patterns
grep -rn --include="*.js" --include="*.ts" \
  -E "(try\s*\{|catch\s*\(|\.catch\(|throw new|Promise\.reject)" . \
  | grep -v "node_modules\|vendor" | head -40

grep -rn --include="*.go" \
  -E "(if err != nil|return err|fmt\.Errorf|errors\.New|errors\.Wrap)" . \
  | grep -v "vendor" | head -40

grep -rn --include="*.py" \
  -E "(except |raise |try:|except Exception)" . \
  | grep -v "test\|spec" | head -40
```

Determine:
1. Is error handling consistent? (try/catch vs callbacks vs Result types)
2. Are errors wrapped with context or thrown raw?
3. What happens with unexpected errors? (panic, log and continue, propagate up?)
4. Are custom error types used? What do they look like?
5. How are errors surfaced to callers/users?

## Phase 3: Code Organization Patterns

```bash
# File length distribution (longer files = monolith preference; shorter = SRP preference)
find . -name "*.js" -o -name "*.ts" -o -name "*.go" -o -name "*.py" 2>/dev/null \
  | grep -v "node_modules\|vendor\|.git" \
  | xargs wc -l 2>/dev/null | sort -rn | head -20

# Function/method length - find long functions
grep -rn --include="*.go" -E "^func " . | grep -v vendor | head -20
```

Determine:
1. Preferred file size (tiny modules vs. larger files)?
2. One class/type per file or grouping by domain?
3. Are utility functions extracted or inlined?
4. Is there a preference for composition vs. inheritance?

## Phase 4: Testing Patterns

Read the test files carefully:

```bash
# Find all test files
find . -name "*.test.*" -o -name "*_test.*" -o -name "*.spec.*" -o -name "*_spec.*" 2>/dev/null \
  | grep -v "node_modules\|vendor\|.git" | head -20

# Sample test structure
grep -rn --include="*.test.*" --include="*_test.*" --include="*.spec.*" \
  -E "(describe|it\(|test\(|func Test|def test_|beforeEach|afterEach|setUp|tearDown)" . \
  | grep -v "node_modules\|vendor" | head -40
```

Read 3-5 representative test files and determine:
1. Unit vs. integration vs. e2e test ratio
2. Test structure (describe/it nesting depth, AAA pattern, etc.)
3. Mocking style (manual mocks, jest.mock, sinon, testify, etc.)
4. What gets tested (happy path only? Edge cases? Error paths?)
5. Test data setup (factories, fixtures, inline?)
6. Assertion style (expect().toBe vs assert.Equal vs assert_that)

## Phase 5: Comment and Documentation Patterns

```bash
# Inline comment frequency and style
grep -rn --include="*.js" --include="*.ts" --include="*.go" --include="*.py" \
  -E "^\s*(//|#|/\*)" . \
  | grep -v "node_modules\|vendor\|test\|spec" | wc -l

# JSDoc / GoDoc / docstrings
grep -rn --include="*.js" --include="*.ts" -E "(/\*\*|\* @param|\* @returns)" . \
  | grep -v "node_modules" | head -20

grep -rn --include="*.go" -E "^// [A-Z]" . | grep -v vendor | head -20
```

Determine:
1. Are public functions/methods documented?
2. What comment style is used?
3. Are there TODO/FIXME comments and do they have ticket references?
4. Is there inline documentation for complex logic?

## Phase 6: Dependency Injection and Wiring Patterns

```bash
# Constructor patterns
grep -rn --include="*.ts" --include="*.js" \
  -E "(constructor\(|@Injectable|@Inject|createApp|new [A-Z])" . \
  | grep -v "node_modules\|test\|spec" | head -30

grep -rn --include="*.go" \
  -E "(func New[A-Z]|wire\.|fx\.|dig\.)" . \
  | grep -v vendor | head -20
```

## Phase 7: Synthesis

Produce a pattern reference document:

**Naming Guide**: Concrete rules derived from observation, with examples from the codebase

**Error Handling Contract**: The expected error handling pattern with a code example

**File Organization Rules**: How to structure new files/modules

**Test Writing Guide**: How to write a test that matches existing style, with template

**Comment Standards**: When to comment and how

**Code Review Checklist**: Based on patterns observed, what would a reviewer here look for?

**Anti-patterns to Avoid**: Patterns you tried but the codebase doesn't use, or places where inconsistency suggests old patterns being phased out

**Template: New Feature Stub**: A skeleton of a new feature that follows all observed conventions

$ARGUMENTS
