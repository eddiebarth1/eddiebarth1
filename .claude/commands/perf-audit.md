Perform a performance audit of this codebase. Identify bottlenecks, inefficient patterns, memory issues, and missed optimization opportunities. Produce concrete, actionable findings with specific file locations - not generic advice.

## Context Bootstrap

Before starting, check whether `/deep-learn` has already been run on this codebase:

```bash
cat .claude-learning-metadata.json 2>/dev/null
cat .claude-learning/manifest.json 2>/dev/null
cat .claude-learning/performance-analyzer.json 2>/dev/null
cat .claude-learning/git-history-miner.json 2>/dev/null
```

**If manifest.json exists**: Use `scope_boundaries.source` to scope all grep commands below. Skip `scope_boundaries.vendor`, `scope_boundaries.generated`, and `scope_boundaries.tests`.

**If performance-analyzer.json exists**: Load prior findings. Focus on extending them — verify listed hotspots are still present, check if any were fixed, and identify new hotspots introduced since the last run.

**If git-history-miner.json exists**: Use `hotspots` (files that change often) to prioritize where to look first — high-churn files with performance issues create the most ongoing drag. Use `ownership_map` to add context about who to route fixes to.

**If no context exists**: Proceed with the phases below, doing full discovery.

## Phase 1: Application Type and Performance Profile

Understand what kind of performance matters here:
1. What type of application is this? (web server, batch processor, CLI, real-time system, etc.)
2. What are the performance-sensitive operations? (HTTP request handling, data processing, queries, etc.)
3. What does "performance" mean here? (latency, throughput, memory, startup time, build time?)

Read the README and any performance-related documentation.

## Phase 2: Database and Query Analysis

Database queries are the most common performance bottleneck:

```bash
# Find all database query sites
grep -rn --include="*.js" --include="*.ts" --include="*.go" --include="*.py" --include="*.rb" \
  -E "(\.query\(|\.find\(|\.findAll\(|\.select\(|\.where\(|db\.|gorm\.|mongoose\.|SELECT|INSERT|UPDATE)" . \
  | grep -v "node_modules\|vendor\|test\|spec" | head -50
```

Look for:
1. **N+1 queries**: Loops that execute queries inside them
2. **Missing indexes**: Queries that filter on columns that likely aren't indexed
3. **SELECT ***: Fetching all columns when only a few are needed
4. **Unbounded queries**: Queries without LIMIT that could return millions of rows
5. **Missing pagination**: APIs that return all records
6. **Repeated identical queries**: Same query called multiple times without caching

Read the ORM model definitions and schema to understand what indexes exist.

## Phase 3: Algorithmic Complexity

Find O(n²) or worse algorithms:

```bash
# Nested loops (potential O(n²))
grep -rn --include="*.go" --include="*.js" --include="*.ts" --include="*.py" \
  -E "for.*\{|for.*in|forEach|\.map\(" . \
  | grep -v "node_modules\|vendor\|test\|spec" | head -30
```

Read any code that processes collections and assess:
1. Are there nested iterations over the same collection?
2. Are there repeated linear scans that could use a map/set?
3. Are sorting operations performed more times than necessary?
4. Are expensive operations performed inside loops that could be hoisted?

## Phase 4: Memory Patterns

```bash
# Find potential memory leaks - event listeners, timers, subscriptions
grep -rn --include="*.js" --include="*.ts" \
  -E "(addEventListener|setInterval|setTimeout|\.on\(|subscribe\()" . \
  | grep -v "node_modules\|test\|spec" | head -30

# Find corresponding cleanup
grep -rn --include="*.js" --include="*.ts" \
  -E "(removeEventListener|clearInterval|clearTimeout|\.off\(|unsubscribe\()" . \
  | grep -v "node_modules\|test\|spec" | head -20
```

For each listener/timer/subscription found, check if a corresponding cleanup exists.

Also look for:
1. Large data structures held in module scope (singleton caches without eviction)
2. Accumulating arrays in long-running processes
3. File handles or connections that may not be closed

## Phase 5: Caching Opportunities

```bash
# Find existing caching
grep -rn --include="*.js" --include="*.ts" --include="*.go" --include="*.py" \
  -E "(cache|redis|memcache|lru|memoize|memo\()" . \
  | grep -v "node_modules\|vendor\|test" | head -20
```

Assess:
1. What expensive computations or queries are performed repeatedly without caching?
2. Are API responses cached at the appropriate layer?
3. Are computed values (like aggregates) recalculated on every request?
4. Is there unnecessary serialization/deserialization?

## Phase 6: Concurrency and Async Patterns

```bash
# Sequential async operations that could be parallelized
grep -rn --include="*.js" --include="*.ts" \
  -E "await.*\n.*await|await.*await" . \
  | grep -v "node_modules\|test\|spec" | head -20

# Go goroutine patterns
grep -rn --include="*.go" \
  -E "(go func|goroutine|WaitGroup|channel|chan)" . \
  | grep -v vendor | head -20
```

Look for:
1. `await a; await b;` where b doesn't depend on a (should be `await Promise.all([a, b])`)
2. Sequential API calls that could be parallelized
3. Missing goroutine pooling for high-concurrency Go code
4. Blocking operations on the main thread

## Phase 7: Build and Startup Performance

```bash
# Bundle analysis indicators
cat package.json 2>/dev/null | grep -E "(bundle|webpack|vite|esbuild|rollup)"

# Import patterns that indicate large bundle size
grep -rn --include="*.ts" --include="*.js" \
  -E "^import .* from '(lodash|moment|rxjs|antd|@mui)'" . \
  | grep -v "node_modules\|test" | head -20
```

Check:
1. Are large libraries imported wholesale instead of tree-shaken?
2. Is code splitting used for web applications?
3. Are there expensive startup operations that could be lazy-loaded?

## Phase 8: Network and I/O Patterns

```bash
# Find HTTP client usage
grep -rn --include="*.js" --include="*.ts" --include="*.go" --include="*.py" \
  -E "(fetch\(|axios\.|http\.Get|requests\.(get|post)|urllib)" . \
  | grep -v "node_modules\|vendor\|test\|spec" | head -20

# File I/O
grep -rn --include="*.js" --include="*.ts" --include="*.go" --include="*.py" \
  -E "(readFile|writeFile|fs\.|os\.ReadFile|ioutil\.)" . \
  | grep -v "node_modules\|vendor\|test\|spec" | head -20
```

Look for:
1. Missing connection pooling for HTTP clients
2. Reading large files entirely into memory
3. Synchronous file I/O in async contexts
4. Missing request timeouts

## Phase 9: Synthesis

Produce a structured performance report:

**Performance Profile**: What type of performance matters for this system and what the expected bottlenecks are.

**Findings** (for each finding):
- **Impact**: High / Medium / Low
- **Category**: (N+1 Query / Memory Leak / Algorithm / Caching / Concurrency / etc.)
- **Location**: `file:line_number`
- **Description**: What the issue is and why it causes a performance problem
- **Proposed Fix**: Specific code change with example

**Quick Wins**: High-impact, low-effort fixes that should be done first.

**Architectural Changes**: Performance improvements that require larger structural changes.

**Measurement Recommendations**: What metrics to instrument and how to measure improvement.

**Benchmarks to Write**: Specific functions or paths that should have benchmarks before and after optimization.

$ARGUMENTS
