Perform a technical debt analysis of this codebase. Surface complexity hotspots, code smells, architectural debt, and risky abstractions. Produce a prioritized list of what to address and in what order - not a laundry list, but a strategic assessment.

## Context Bootstrap

Before starting, check whether `/deep-learn` has already been run on this codebase:

```bash
cat .claude-learning-metadata.json 2>/dev/null
cat .claude-learning/manifest.json 2>/dev/null
cat .claude-learning/codebase-indexer.json 2>/dev/null
cat .claude-learning/git-history-miner.json 2>/dev/null
cat .claude-learning/edge-failure-mapper.json 2>/dev/null
```

**If manifest.json exists**: Use `scope_boundaries.source` to scope all grep commands — skip vendor/generated/test paths.

**If codebase-indexer.json exists**: Use `modules` for the list of files to assess. Use `conventions` to identify deviations (code that doesn't follow established patterns is a form of debt). Use `patterns.architecture` to identify structural mismatches.

**If git-history-miner.json exists**: Use `hotspots` (high-churn files) as your top-priority debt candidates — files that change often and have complexity are the most expensive debt to carry. Use `inline_knowledge` (TODO/FIXME/HACK comments) as self-documented debt — these are guaranteed finds for Phase 2. Use `decisions` to distinguish intentional architectural choices from unintentional accumulation.

**If edge-failure-mapper.json exists**: Use `uncovered_edges` and high-severity `failure_modes` as a debt signal — unhandled failure paths are reliability debt. Use `validation_rules` to identify where input handling is inconsistent.

**If no context exists**: Proceed with the phases below, doing full discovery.

## Phase 1: Complexity Hotspots

Find the most complex code in the codebase:

```bash
# Files with the most lines of code
find . -name "*.js" -o -name "*.ts" -o -name "*.go" -o -name "*.py" -o -name "*.rb" 2>/dev/null \
  | grep -v "node_modules\|vendor\|.git\|test\|spec" \
  | xargs wc -l 2>/dev/null | sort -rn | head -20

# Functions/methods over 50 lines (high cognitive complexity)
# For Go:
grep -n "^func " **/*.go 2>/dev/null | head -50

# For JavaScript/TypeScript - find large function bodies
grep -rn --include="*.js" --include="*.ts" \
  -E "^(export\s+)?(async\s+)?function\s+\w+|^\s+(async\s+)?\w+\s*\([^)]*\)\s*\{" . \
  | grep -v "node_modules\|test\|spec" | head -40
```

Read the largest, most complex files and assess:
1. Does this file have a single clear responsibility?
2. How many branches/conditions does the core logic have?
3. Are there deeply nested conditionals (more than 3 levels)?
4. Are there functions longer than ~30 lines?

## Phase 2: Code Smell Detection

Search for common code smells:

```bash
# Magic numbers and strings
grep -rn --include="*.js" --include="*.ts" --include="*.go" --include="*.py" \
  -E "\b(86400|3600|1000|60|24|365|404|500|200)\b" . \
  | grep -v "node_modules\|vendor\|test\|spec\|const\|_test" | head -20

# Long parameter lists (more than 4 params often indicates a data object is needed)
grep -rn --include="*.go" \
  -E "^func \w+\([^)]{80,}\)" . | grep -v vendor | head -20

grep -rn --include="*.ts" --include="*.js" \
  -E "function\s+\w+\s*\([^)]{80,}\)" . | grep -v "node_modules\|test" | head -20

# TODO/FIXME/HACK comments - these are self-documented debt
grep -rn --include="*.js" --include="*.ts" --include="*.go" --include="*.py" --include="*.rb" \
  -E "(TODO|FIXME|HACK|XXX|TEMP|WORKAROUND|KLUDGE)" . \
  | grep -v "node_modules\|vendor\|.git" | head -40

# Commented-out code blocks
grep -rn --include="*.js" --include="*.ts" --include="*.go" \
  -E "^\s*//.*[;{}]|^\s*#.*[=:()]" . \
  | grep -v "node_modules\|vendor\|.git" | head -20
```

## Phase 3: Duplication Detection

Find areas of significant code duplication:

```bash
# Similar function signatures that might indicate copy-paste
grep -rn --include="*.go" --include="*.ts" --include="*.js" --include="*.py" \
  -E "(function|func|def)\s+\w*(Get|Fetch|Find|Create|Update|Delete)\w*" . \
  | grep -v "node_modules\|vendor\|test\|spec" | sort | head -40
```

Read areas with suspicious similarity and assess whether they should be extracted into shared utilities.

## Phase 4: Coupling and Dependency Issues

```bash
# Files that import from many other internal modules (high coupling)
grep -rn --include="*.ts" --include="*.js" \
  -E "^import.*from\s+['\"]\.\.?/" . \
  | grep -v "node_modules\|test\|spec" \
  | awk -F: '{print $1}' | sort | uniq -c | sort -rn | head -20

# Circular dependency indicators
grep -rn --include="*.go" \
  -E "^import\s+\(" . | grep -v vendor | head -20
```

Assess:
1. Are there files that everyone imports? (god objects)
2. Are there circular dependencies?
3. Is business logic leaking into the wrong layer?

## Phase 5: Test Coverage Gaps

```bash
# Files with no corresponding test
find . -name "*.go" -not -name "*_test.go" | grep -v vendor | while read f; do
  base=$(basename "$f" .go)
  dir=$(dirname "$f")
  if [ ! -f "$dir/${base}_test.go" ]; then echo "UNTESTED: $f"; fi
done 2>/dev/null | head -20

# Test-to-code ratio
echo "Source files:"
find . -name "*.go" -not -name "*_test.go" | grep -v vendor | wc -l
echo "Test files:"
find . -name "*_test.go" | grep -v vendor | wc -l
```

## Phase 6: Stale and Dead Code

```bash
# Exported symbols that are never used internally (may be dead)
# Find all exported function names and check if they're used
grep -rn --include="*.go" -E "^func [A-Z]\w+" . | grep -v vendor | head -30

# Find unused imports
grep -rn --include="*.py" -E "^import |^from.*import" . \
  | grep -v "test\|spec" | head -30

# Old/abandoned directories or config
find . -name "*.bak" -o -name "*.old" -o -name "*.orig" 2>/dev/null | grep -v ".git"
find . -type d -name "deprecated*" -o -name "old*" -o -name "archived*" 2>/dev/null | grep -v ".git\|node_modules"
```

## Phase 7: Synthesis

Produce a prioritized debt report:

**Debt Severity Matrix**:
| Item | Location | Type | Effort to Fix | Risk if Ignored | Priority |
|---|---|---|---|---|---|

**Critical Debt** (fix before next major feature):
- Items that introduce correctness risks or make changes dangerous

**High Debt** (plan for next quarter):
- Complexity that significantly slows development velocity

**Medium Debt** (address opportunistically):
- Code smells that can be cleaned up while working nearby

**Low Debt** (backlog):
- Cosmetic or minor issues

**Self-Documented Debt**: All TODO/FIXME/HACK comments with assessment of which ones are actually important

**Refactoring Roadmap**: Sequenced plan for addressing the most impactful debt

**Keep/Discard List**: Code that appears stale or unused and can likely be deleted

$ARGUMENTS
