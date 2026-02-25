# deep-learn
Full codebase intelligence pass using specialized parallel agents. Builds a tiered knowledge artifact — institutional context, structural map, and retrieval recipes — stored as a named skill and a CLAUDE.md.

## Usage
```
/deep-learn <target-path> [--name <project-name>] [--update] [--force]
```

**Arguments:**
- `target-path`: Directory to analyze (relative or absolute). Defaults to current directory if omitted.
- `--name`: Custom name for the generated skill (defaults to directory name)
- `--update`: Incremental mode — only analyze changes since last run
- `--force`: Force full re-run even when `--update` finds no changes

**Examples:**
```
/deep-learn .
/deep-learn ./services/payments --name payments-api
/deep-learn ./services/payments --update
/deep-learn . --update --force
```

---

## Design Principles

**Retrieval-first**: Agents use targeted grep/glob to pull what they need surgically. No bulk file loading.

**JSON intermediates**: Every agent writes structured JSON to `.claude-learning/`. The synthesizer reads selectively — no context dumping between phases.

**Scope boundaries are first-class**: Each agent has explicit INCLUDE/EXCLUDE rules. They only read what their specialty requires.

**Tiered knowledge**: Generated artifacts separate three tiers:
- **Tier 1 — Institutional**: Decisions, gotchas, conventions, implicit contracts. Stable. Hard to reconstruct. Written in full.
- **Tier 2 — Structural**: Module index, dependency graph, risk map, ownership, test coverage. Semi-stable.
- **Tier 3 — Retrieval recipes**: Grep/glob/git commands to find current implementation details. Always executed fresh — never cached as facts.

**Thin orchestration**: This command routes agents and scopes work. Agents write files. The synthesizer reads files. You do not see raw agent output.

---

## Instructions

You are orchestrating a codebase intelligence pipeline. Follow these phases exactly.

---

### Phase 0: Input Validation and Mode Detection

1. Parse `$ARGUMENTS`:
   - Extract `target-path` (default to `.` if omitted)
   - Extract `--name` if provided; otherwise derive from the last path segment
   - Extract `--update` flag
   - Extract `--force` flag
   - Sanitize name: lowercase, replace spaces and special chars with hyphens

2. Verify the target path exists and is a directory. If not, stop with a clear error.

3. Resolve to absolute path. Store:
   - `TARGET_PATH` — absolute path to directory
   - `SERVICE_NAME` — sanitized project name
   - `UPDATE_MODE` — true if `--update` present
   - `FORCE_MODE` — true if `--force` present
   - `LEARNING_DIR` — `{TARGET_PATH}/.claude-learning/`
   - `METADATA_FILE` — `{TARGET_PATH}/.claude-learning-metadata.json`

4. Create the learning directory:
   ```bash
   mkdir -p {TARGET_PATH}/.claude-learning
   ```

5. Check for existing metadata:
   ```bash
   cat {TARGET_PATH}/.claude-learning-metadata.json 2>/dev/null
   ```
   If found, extract: `LAST_LEARNED_DATE`, `LAST_LEARNED_COMMIT`, `PREVIOUS_AGENTS_RUN`.

6. **If `--update` but no metadata**: notify user, set `UPDATE_MODE` to false and proceed as full run.

7. **If `--update` and metadata found**: proceed to Phase 0.5 (Change Detection).

---

### Phase 0.1: Manifest Generation (Routing Layer)

Build a lightweight structural map before any agents run. **Do NOT read file contents — only file names and package metadata.**

1. **Directory scan** (structure only):
   ```bash
   find {TARGET_PATH} -type f \
     -not -path '*/node_modules/*' \
     -not -path '*/.git/*' \
     -not -path '*/dist/*' \
     -not -path '*/build/*' \
     -not -path '*/__pycache__/*' \
     -not -path '*/vendor/*' \
     -not -path '*/.claude-learning/*' \
     | head -1000
   ```

2. **Language/framework detection** (package files only):
   ```bash
   ls {TARGET_PATH}/package.json \
      {TARGET_PATH}/Cargo.toml \
      {TARGET_PATH}/go.mod \
      {TARGET_PATH}/pyproject.toml \
      {TARGET_PATH}/setup.py \
      {TARGET_PATH}/Gemfile \
      {TARGET_PATH}/pom.xml \
      {TARGET_PATH}/build.gradle \
      {TARGET_PATH}/mix.exs \
      {TARGET_PATH}/composer.json 2>/dev/null
   ```
   Read whichever package file exists to extract language, framework, and external dependencies.

3. **Scope boundary detection** — identify:
   - Test dirs: `test/`, `tests/`, `__tests__/`, `spec/`, `*_test.go`, `*.test.*`, `*.spec.*`
   - Vendor/deps: `node_modules/`, `vendor/`, `dist/`, `build/`, `.next/`, `target/`
   - Generated: `*.generated.*`, `*_gen.*`, `generated/`, `__generated__/`
   - Config: `*.config.*`, `.env*`, `docker-compose*`, `Dockerfile*`
   - Entry points: `main.*`, `index.*`, `app.*`, `server.*`, `__init__.py`, `mod.rs`, `lib.rs`

4. **Write manifest** to `{TARGET_PATH}/.claude-learning/manifest.json`:
   ```json
   {
     "root": "{TARGET_PATH}",
     "language": "...",
     "framework": "...",
     "package_manager": "...",
     "entry_points": ["..."],
     "scope_boundaries": {
       "source": ["..."],
       "tests": ["..."],
       "config": ["..."],
       "vendor": ["..."],
       "generated": ["..."]
     },
     "file_count": 0,
     "top_level_modules": ["..."],
     "external_dependencies": ["..."]
   }
   ```

This manifest is passed to every agent as their routing table.

---

### Phase 0.5: Change Detection (UPDATE_MODE only)

```bash
git -C {TARGET_PATH} log --oneline {LAST_LEARNED_COMMIT}..HEAD -- .
git -C {TARGET_PATH} diff --name-only {LAST_LEARNED_COMMIT}..HEAD -- .
git -C {TARGET_PATH} diff --stat {LAST_LEARNED_COMMIT}..HEAD -- .
```

Determine which agents need to re-run:

| Change type | Agents to run |
|---|---|
| File structure changes (new/deleted/moved) | codebase-indexer |
| Import or dependency changes | dependency-mapper |
| Any code changes | edge-failure-mapper, security-mapper, performance-analyzer |
| Test file changes | test-fixtures-miner |
| Any commits | git-history-miner (always) |

Store `CHANGED_FILES`, `AGENTS_TO_RUN`, `CHANGE_SUMMARY`.

If no meaningful changes detected and `FORCE_MODE` is false:
- Inform user: "No significant changes since {LAST_LEARNED_DATE}. Knowledge is current."
- Offer: "Run with `--force` to refresh anyway."
- Exit.

---

### Phase 1: Parallel Agent Analysis

**Full mode**: launch all seven agents in parallel.
**Update mode**: launch only `AGENTS_TO_RUN`, with prompts scoped to `CHANGED_FILES`.

Replace `{MANIFEST_JSON}` with the actual contents of `{TARGET_PATH}/.claude-learning/manifest.json` when constructing each prompt. Launch using the Task tool.

---

#### Agent 1: codebase-indexer

```
You are analyzing the codebase structure at {TARGET_PATH}.

## Manifest (your routing table)
{MANIFEST_JSON}

## Scope
INCLUDE: Files in scope_boundaries.source, entry points from manifest, config files
EXCLUDE: scope_boundaries.tests, scope_boundaries.vendor, scope_boundaries.generated — do NOT read these.

## Retrieval Strategy

Pass 1 — Discovery:
- Glob all files in each source directory
- Grep for module/class/function definitions (export, class, function, def, fn, func, pub)
- Grep for configuration patterns (env vars, config reads, feature flags)
- Read ONLY the entry point files listed in the manifest

Pass 2 — Deep Dive:
- For each top-level module, read only its entry/index file (first 50 lines) to understand its interface
- For each pattern found in Pass 1, read surrounding context using line ranges — not full files
- For each convention pattern (naming, organization, error handling), collect 2-3 file:line examples

## Output
Write structured JSON to {TARGET_PATH}/.claude-learning/codebase-indexer.json

Schema:
{
  "summary": "2-3 sentence overview",
  "modules": [
    {
      "path": "relative/path/",
      "purpose": "...",
      "entry_point": "index.ts",
      "key_exports": ["..."],
      "internal_structure": "..."
    }
  ],
  "patterns": {
    "architecture": "...",
    "naming": "...",
    "file_organization": "...",
    "error_handling": "..."
  },
  "conventions": [
    {
      "rule": "...",
      "evidence": ["file:line", "file:line"],
      "confidence": "high|medium"
    }
  ],
  "entry_points": [
    {"file": "...", "line": 1, "purpose": "..."}
  ],
  "config_patterns": [
    {"type": "env_var|config_file|feature_flag", "name": "...", "location": "file:line"}
  ]
}

Write valid JSON only. No prose.
```

---

#### Agent 2: dependency-mapper

```
You are mapping dependencies for the codebase at {TARGET_PATH}.

## Manifest
{MANIFEST_JSON}

## Scope
INCLUDE: Import/require/use statements in scope_boundaries.source, package files, API route definitions, config files referencing external services
EXCLUDE: Implementation bodies (you care about WHAT is imported, not HOW it's used), scope_boundaries.tests, scope_boundaries.vendor

## Retrieval Strategy

Pass 1 — Discovery:
- Read the package file for all external dependencies
- Grep source dirs for import patterns:
  - JS/TS: `import .* from|require\(`
  - Python: `^import |^from .* import`
  - Go: `import \(`
  - Rust: `^use |^mod `
- Grep for API route definitions (app.get, router.post, @Route, @Controller, @GetMapping, etc.)
- Grep for external service calls (fetch, axios, http.get, grpc, database queries, queue publishes)

Pass 2 — Deep Dive:
- For the most-imported internal modules, read only the top of the file (exports/interface, not implementation)
- For external service calls, read surrounding context to understand the contract
- For route definitions, read the handler signature and middleware chain
- Identify coupling hotspots: modules that import each other or have many cross-imports

## Output
Write structured JSON to {TARGET_PATH}/.claude-learning/dependency-mapper.json

Schema:
{
  "summary": "2-3 sentence overview",
  "external_deps": [
    {
      "name": "...",
      "version": "...",
      "used_by": ["..."],
      "purpose": "..."
    }
  ],
  "external_services": [
    {
      "name": "...",
      "type": "database|api|queue|cache|storage",
      "locations": ["file:line"],
      "protocol": "http|grpc|sql|redis|amqp|etc"
    }
  ],
  "api_surface": [
    {
      "route": "/path",
      "method": "GET|POST|etc",
      "handler": "file:line",
      "middleware": ["..."],
      "description": "..."
    }
  ],
  "coupling_hotspots": [
    {
      "modules": ["module_a", "module_b"],
      "cross_imports": 0,
      "risk": "high|medium|low",
      "description": "..."
    }
  ],
  "implicit_contracts": [
    {
      "provider": "...",
      "consumer": "...",
      "contract": "What is assumed",
      "evidence": "file:line"
    }
  ]
}

Write valid JSON only. No prose.
```

---

#### Agent 3: git-history-miner

```
You are mining institutional knowledge from the git history of {TARGET_PATH}.

## Manifest
{MANIFEST_JSON}

## Scope
PRIMARY: Git metadata — git log, git blame, git shortlog. Use git commands heavily.
SECONDARY: Inline comments (TODO, FIXME, HACK, NOTE, WARN, WORKAROUND) via targeted grep.
EXCLUDE: Do NOT read full source files. Extract knowledge from git history and comments only.

## Retrieval Strategy

Pass 1 — Decision Mining (git metadata only):
1. Full commit log:
   git -C {TARGET_PATH} log --all --oneline -- .

2. Decision-bearing commits (explain WHY):
   git -C {TARGET_PATH} log --all --grep="why\|because\|decision\|trade-off\|instead of\|revert\|migrate\|refactor\|breaking\|deprecat" -i --format='%H|%an|%ad|%s' -- .

3. High-churn commits (many files = architectural change):
   git -C {TARGET_PATH} log --all --format='%H %s' --shortstat -- .

4. Revert commits (always carry "why not" context):
   git -C {TARGET_PATH} log --all --grep="revert\|Revert" --format='%H|%an|%ad|%s' -- .

5. Contributor weight per module:
   For each top_level_module: git -C {TARGET_PATH} shortlog -sn --all -- {module}/

6. Change hotspots (most-modified files):
   git -C {TARGET_PATH} log --all --format='%H' -- . | while read sha; do git diff-tree --no-commit-id --name-only -r $sha; done | sort | uniq -c | sort -rn | head -30

Pass 2 — Context Extraction:
1. For decision-bearing commits found in Pass 1:
   - Read full commit message: git -C {TARGET_PATH} log -1 --format='%B' {sha}
   - Get file list: git -C {TARGET_PATH} show {sha} --stat

2. Code-embedded knowledge (targeted grep, not full file reads):
   - grep for TODO|FIXME|HACK|NOTE|WARN|XXX|IMPORTANT|CAUTION|WORKAROUND in scope_boundaries.source
   - grep for "workaround|intentional|temporary|legacy|deprecated|do not|don't|never|always|must" in comment lines
   - For each finding, record file:line and comment text

## Output
Write structured JSON to {TARGET_PATH}/.claude-learning/git-history-miner.json

Schema:
{
  "summary": "2-3 sentence overview of history and institutional context",
  "decisions": [
    {
      "commit": "sha",
      "date": "...",
      "author": "...",
      "decision": "What was decided",
      "rationale": "Why",
      "affected_modules": ["..."],
      "still_relevant": true
    }
  ],
  "gotchas": [
    {
      "source": "commit_message|code_comment|revert_commit",
      "location": "file:line",
      "commit": "sha",
      "description": "What will bite you",
      "author": "...",
      "date": "..."
    }
  ],
  "inline_knowledge": [
    {
      "file": "relative/path:line",
      "type": "TODO|FIXME|HACK|NOTE|WARN|WORKAROUND",
      "content": "The comment text",
      "author": "..."
    }
  ],
  "evolution_patterns": [
    {
      "pattern": "e.g. gateway.ts and webhook.ts always change together",
      "evidence": "...",
      "implication": "..."
    }
  ],
  "contributors": [
    {
      "name": "...",
      "total_commits": 0,
      "primary_areas": ["..."],
      "expertise": "..."
    }
  ],
  "hotspots": [
    {
      "file": "...",
      "change_frequency": 0,
      "last_changed": "...",
      "significance": "..."
    }
  ],
  "ownership_map": {
    "module/path/": {
      "primary": "...",
      "secondary": ["..."],
      "total_commits": 0
    }
  }
}

Write valid JSON only. No prose.
```

---

#### Agent 4: edge-failure-mapper

```
You are analyzing edge cases and failure modes in the codebase at {TARGET_PATH}.

## Manifest
{MANIFEST_JSON}

## Scope
INCLUDE: Error handling, validation, boundary code, catch blocks, error types, resilience patterns in scope_boundaries.source
EXCLUDE: Happy-path implementation, scope_boundaries.tests, scope_boundaries.vendor, scope_boundaries.generated

## Retrieval Strategy

Pass 1 — Discovery (grep across source dirs):
- Error handling: `catch|except|rescue|recover|on_error|fallback`
- Validation: `validate|validator|sanitize|assert|guard|ensure|constraint`
- Error types: `Error|Exception|Err\(|Result<|Option<|Maybe|Either`
- Resilience: `timeout|retry|circuit.?breaker|rate.?limit|deadline|backoff`
- Unsafe exits: `panic|fatal|abort|process\.exit|os\.Exit|unwrap\(\)`
- Null safety: `null|nil|undefined|None|Optional|nullable`
- Intentionality markers: `intentional|expected|accepted|won't fix|by design|trade-off`

Pass 2 — Deep Dive:
- For each finding, read the surrounding code using line ranges (the catch block + a few lines of context, not the full file)
- Categorize: well-handled, partial handling, or uncovered edge case?
- Assess blast radius using dependency info from the manifest modules

## Output
Write structured JSON to {TARGET_PATH}/.claude-learning/edge-failure-mapper.json

Schema:
{
  "summary": "2-3 sentence overview of error handling maturity and key risks",
  "failure_modes": [
    {
      "location": "file:line",
      "type": "unhandled_error|partial_handling|race_condition|null_reference|timeout|resource_leak|data_corruption",
      "severity": "critical|high|medium|low",
      "description": "What can go wrong",
      "blast_radius": "What else breaks"
    }
  ],
  "error_patterns": [
    {
      "pattern": "...",
      "locations": ["file:line"],
      "handling_strategy": "throw|return|log|retry|etc",
      "is_intentional": true
    }
  ],
  "uncovered_edges": [
    {
      "location": "file:line",
      "scenario": "What is not handled",
      "risk": "What could happen",
      "recommendation": "..."
    }
  ],
  "resilience_patterns": [
    {
      "pattern": "retry|circuit_breaker|fallback|timeout|rate_limit",
      "locations": ["file:line"],
      "description": "...",
      "configuration": "timeout values, retry counts, etc."
    }
  ],
  "validation_rules": [
    {
      "location": "file:line",
      "what_is_validated": "...",
      "rules": ["..."],
      "on_failure": "..."
    }
  ]
}

Write valid JSON only. No prose.
```

---

#### Agent 5: security-mapper

```
You are performing a security analysis of the codebase at {TARGET_PATH}.

## Manifest
{MANIFEST_JSON}

## Scope
INCLUDE: Authentication, authorization, input handling, data access, cryptography, secrets management, and HTTP/API boundaries in scope_boundaries.source and scope_boundaries.config
EXCLUDE: scope_boundaries.vendor, scope_boundaries.generated, scope_boundaries.tests (unless tests reveal security anti-patterns)

## Retrieval Strategy

Pass 1 — Discovery (grep across source dirs):
- Injection surfaces: `query\(|execute\(|eval\(|exec\(|spawn\(|innerHTML|dangerouslySetInnerHTML|render_template_string`
- Auth patterns: `jwt|token|session|cookie|oauth|bearer|password|hash|bcrypt|argon|scrypt`
- Secrets in code: `api_key|secret|password|private_key|client_secret` (looking for hardcoded values, not variable names)
- Crypto: `md5|sha1|des\b|rc4|Math\.random|rand\(\)` (weak algorithms)
- HTTP security headers: `helmet|cors|csp|x-frame|strict-transport`
- File operations: `readFile|writeFile|unlink|path\.join|__dirname`
- Deserialization: `JSON\.parse|pickle\.loads|yaml\.load|unserialize|Marshal\.load`
- Env/config: grep scope_boundaries.config for hardcoded secrets

Pass 2 — Deep Dive:
- For each injection surface, read surrounding context (10-15 lines) to assess if input is sanitized
- For auth patterns, read surrounding context to assess token validation, expiry, and privilege checks
- For any apparent hardcoded secrets (not env-var references), read to confirm
- For crypto patterns, read to assess key sizes, algorithm choices, and randomness sources
- Cross-reference the api_surface from dependency-mapper: for each endpoint, assess auth coverage

## Output
Write structured JSON to {TARGET_PATH}/.claude-learning/security-mapper.json

Schema:
{
  "summary": "2-3 sentence overview of security posture and top risks",
  "findings": [
    {
      "location": "file:line",
      "category": "injection|broken_auth|sensitive_data|xxe|broken_access|security_misconfiguration|xss|insecure_deserialization|known_vuln|insufficient_logging",
      "severity": "critical|high|medium|low|info",
      "title": "Short title",
      "description": "What the issue is",
      "attack_vector": "How an attacker could exploit this",
      "recommendation": "Concrete fix"
    }
  ],
  "auth_coverage": {
    "mechanism": "jwt|session|oauth|api_key|none|...",
    "unprotected_routes": ["file:line route definition"],
    "privilege_escalation_risks": ["file:line"],
    "session_management": "description of session handling"
  },
  "secrets_audit": {
    "hardcoded_secrets": ["file:line"],
    "env_var_usage": "good|partial|none",
    "secrets_in_config_files": ["file:line"]
  },
  "crypto_assessment": {
    "weak_algorithms": ["file:line — algorithm used"],
    "key_management": "description",
    "randomness": "secure|insecure|mixed"
  },
  "input_handling": {
    "validated_boundaries": ["file:line"],
    "unvalidated_inputs": ["file:line"],
    "sanitization_gaps": ["file:line"]
  },
  "dependency_risks": [
    {
      "package": "...",
      "concern": "known CVE|abandoned|overprivileged",
      "severity": "high|medium|low"
    }
  ]
}

Write valid JSON only. No prose.
```

---

#### Agent 6: performance-analyzer

```
You are performing a performance analysis of the codebase at {TARGET_PATH}.

## Manifest
{MANIFEST_JSON}

## Scope
INCLUDE: Database queries, loops, data loading patterns, caching, async/concurrency, and algorithmic complexity in scope_boundaries.source
EXCLUDE: scope_boundaries.vendor, scope_boundaries.generated, scope_boundaries.tests

## Retrieval Strategy

Pass 1 — Discovery (grep across source dirs):
- Database patterns: `SELECT|INSERT|UPDATE|DELETE|find\(|findAll\(|query\(|aggregate\(`
- N+1 risks: loops containing db calls — look for db/ORM calls inside `for|while|forEach|map`
- Missing pagination: `findAll\(|SELECT \*` without `LIMIT|limit|take|paginate`
- Blocking I/O in async: `await` inside loops, synchronous fs/network calls in async code
- Large data loads: `readFileSync|loadAll|fetchAll|getAll` patterns
- Caching: `cache|redis|memcache|lru|memoize|memo`
- Expensive operations: `sort\(|filter\(|reduce\(|JSON\.parse|JSON\.stringify` on potentially large data
- Timeouts and resource limits: `timeout|maxSize|maxLength|rateLimit`
- Memory patterns: large allocations, unbounded buffers, event listener leaks

Pass 2 — Deep Dive:
- For N+1 candidates (db call inside loop): read 20 lines of context to confirm the pattern
- For large data loads: read surrounding context to check if pagination or streaming is used
- For missing indexes: read schema files or ORM model definitions to check indexed fields
- For caching patterns: read surrounding code to understand what is cached and TTL strategy

## Output
Write structured JSON to {TARGET_PATH}/.claude-learning/performance-analyzer.json

Schema:
{
  "summary": "2-3 sentence overview of performance posture and top risks",
  "hotspots": [
    {
      "location": "file:line",
      "type": "n_plus_one|missing_index|unbounded_query|blocking_io|large_allocation|expensive_serialization|missing_pagination|sync_in_async",
      "severity": "critical|high|medium|low",
      "description": "What the issue is",
      "estimated_impact": "What happens at scale",
      "recommendation": "Concrete fix"
    }
  ],
  "caching_assessment": {
    "strategy": "none|partial|comprehensive",
    "cached_areas": ["..."],
    "uncached_hot_paths": ["file:line"],
    "recommendations": ["..."]
  },
  "database_patterns": {
    "orm_or_driver": "...",
    "query_patterns": ["description of how queries are constructed"],
    "n_plus_one_risks": ["file:line"],
    "missing_pagination": ["file:line"],
    "transaction_usage": "good|partial|none"
  },
  "async_patterns": {
    "concurrency_model": "async/await|promises|threads|goroutines|actors|etc",
    "blocking_risks": ["file:line"],
    "parallelization_opportunities": ["file:line"]
  },
  "resource_management": {
    "connection_pooling": "yes|no|unknown",
    "resource_leaks": ["file:line"],
    "unbounded_collections": ["file:line"]
  }
}

Write valid JSON only. No prose.
```

---

#### Agent 7: test-fixtures-miner

```
You are analyzing the test infrastructure for the codebase at {TARGET_PATH}.

## Manifest
{MANIFEST_JSON}

## Scope
INCLUDE: Files in scope_boundaries.tests, fixture directories, test configuration files, test helpers
EXCLUDE: scope_boundaries.source (you analyze tests, not the code under test), scope_boundaries.vendor, scope_boundaries.generated

## Retrieval Strategy

Pass 1 — Discovery:
- Glob all files in test directories from the manifest
- Grep for test framework patterns:
  - JS/TS: `describe\(|it\(|test\(|expect\(|jest|mocha|vitest|cypress`
  - Python: `def test_|@pytest.fixture|@fixture|conftest`
  - Go: `func Test|t\.Run|testify`
  - Rust: `#\[test\]|#\[cfg\(test\)\]`
- Find fixture dirs: `fixtures/`, `__fixtures__/`, `testdata/`, `test_data/`, `mocks/`, `__mocks__/`, `factories/`
- Find test config: `jest.config`, `pytest.ini`, `.mocharc`, `vitest.config`, `cypress.config`

Pass 2 — Deep Dive:
- Read test config files fully
- For fixture dirs, list contents and read representative fixtures
- Read test helper/utility files
- For each test dir, read one representative test file to understand patterns
- Note coverage configuration and any coverage reports

## Output
Write structured JSON to {TARGET_PATH}/.claude-learning/test-fixtures-miner.json

Schema:
{
  "summary": "2-3 sentence overview of test infrastructure",
  "test_organization": {
    "framework": "...",
    "run_command": "exact command to run all tests",
    "config_file": "relative/path",
    "structure": "co-located|separate directory|etc",
    "conventions": {
      "naming": "...",
      "grouping": "...",
      "setup_teardown": "..."
    }
  },
  "fixtures": [
    {
      "path": "...",
      "purpose": "...",
      "format": "json|yaml|sql|factory|etc",
      "data_patterns": "..."
    }
  ],
  "test_helpers": [
    {
      "path": "...",
      "purpose": "...",
      "key_functions": ["..."]
    }
  ],
  "coverage_assessment": {
    "well_tested": [
      {"module": "...", "evidence": "..."}
    ],
    "gaps": [
      {"module": "...", "gap_type": "no_tests|minimal_tests|missing_edge_cases", "description": "..."}
    ]
  },
  "test_patterns": [
    {
      "pattern": "...",
      "example_location": "file:line",
      "description": "..."
    }
  ]
}

Write valid JSON only. No prose.
```

---

### Phase 1.5: Cross-Service Discovery

After Phase 1 completes, analyze cross-service relationships.

Read the dependency-mapper output:
```bash
cat {TARGET_PATH}/.claude-learning/dependency-mapper.json
```

Check the global service registry:
```bash
cat ~/.claude/learned-services-registry.json 2>/dev/null \
  || echo '{"version":"1.0","services":{},"dependency_graph":{"edges":[]}}'
```

Based on `external_services` and `implicit_contracts` from dependency-mapper, cross-reference against the registry. Write results to `{TARGET_PATH}/.claude-learning/cross-service.json`:

```json
{
  "known_related_services": [
    {
      "service_name": "...",
      "relationship_type": "imports|calls|extends|implements|routes",
      "description": "...",
      "evidence": ["file:line"]
    }
  ],
  "unknown_dependencies": [
    {
      "name": "...",
      "relationship_type": "...",
      "description": "Not yet learned — run /deep-learn on it",
      "evidence": ["file:line"]
    }
  ],
  "external_services": [
    {
      "name": "...",
      "type": "payment_api|auth_provider|storage|email|etc",
      "evidence": ["file:line"]
    }
  ]
}
```

---

### Phase 2: Synthesis

Launch a **codebase-intelligence-synthesizer** agent. This agent reads from the intermediate JSON files — do NOT dump agent outputs into the prompt.

```
You are synthesizing analysis results for {TARGET_PATH} into a unified intelligence report.

## Manifest
{MANIFEST_JSON}

## Instructions
All agent outputs are at {TARGET_PATH}/.claude-learning/. Read them selectively.

Step 1 — Read each file's "summary" field first:
  cat {TARGET_PATH}/.claude-learning/codebase-indexer.json       (read summary field)
  cat {TARGET_PATH}/.claude-learning/dependency-mapper.json      (read summary field)
  cat {TARGET_PATH}/.claude-learning/git-history-miner.json      (read summary field)
  cat {TARGET_PATH}/.claude-learning/edge-failure-mapper.json    (read summary field)
  cat {TARGET_PATH}/.claude-learning/security-mapper.json        (read summary field)
  cat {TARGET_PATH}/.claude-learning/performance-analyzer.json   (read summary field)
  cat {TARGET_PATH}/.claude-learning/test-fixtures-miner.json    (read summary field)
  cat {TARGET_PATH}/.claude-learning/cross-service.json

Step 2 — Deep-dive into specific cross-cutting combinations:
  - git-history-miner hotspots × edge-failure-mapper failure_modes → files that change often AND have unhandled errors = highest risk
  - dependency-mapper coupling_hotspots × git-history-miner ownership_map → tightly coupled modules owned by different people = coordination risk
  - test-fixtures-miner coverage gaps × edge-failure-mapper failure_modes → untested code with known failure modes = critical gap
  - security-mapper findings × dependency-mapper api_surface → unprotected routes with injection surfaces = critical exposure
  - performance-analyzer hotspots × git-history-miner hotspots → slow code that also changes often = compound drag
  - dependency-mapper implicit_contracts × edge-failure-mapper uncovered_edges → assumed contracts with no error handling = hidden fragility

Step 3 — Produce a tiered synthesis.

## Output
Write to {TARGET_PATH}/.claude-learning/synthesis.json

Schema:
{
  "summary": "3-5 sentence executive summary",
  "tier1_institutional_knowledge": {
    "decisions": ["from git-history-miner.decisions"],
    "gotchas": ["merged from git-history-miner.gotchas + edge-failure-mapper failure_modes with severity critical/high"],
    "conventions": ["from codebase-indexer.conventions"],
    "implicit_contracts": ["from dependency-mapper.implicit_contracts"],
    "inline_knowledge": ["from git-history-miner.inline_knowledge — notable TODO/FIXME/HACK with context"],
    "evolution_patterns": ["from git-history-miner.evolution_patterns"]
  },
  "tier2_structural_map": {
    "module_index": ["from codebase-indexer.modules"],
    "dependency_graph": {"from dependency-mapper — key internal and external"},
    "api_surface": ["from dependency-mapper.api_surface"],
    "risk_map": ["severity-ranked from edge-failure-mapper.failure_modes"],
    "security_findings": ["severity-ranked from security-mapper.findings"],
    "performance_hotspots": ["severity-ranked from performance-analyzer.hotspots"],
    "test_coverage": {"from test-fixtures-miner.coverage_assessment"},
    "ownership": {"from git-history-miner.ownership_map"}
  },
  "tier3_retrieval_recipes": {
    "by_module": {
      "module/path/": {
        "main_logic": "grep pattern",
        "error_handling": "grep pattern",
        "tests": "glob pattern",
        "api_surface": "grep pattern",
        "recent_changes": "git log command"
      }
    },
    "by_task": {
      "trace_a_request": "grep patterns to follow a request through the system",
      "find_validation": "grep patterns to find all validation rules",
      "find_auth_checks": "grep patterns to find authorization logic",
      "find_db_queries": "grep patterns to find all database interactions",
      "find_config": "grep patterns to find configuration",
      "find_errors": "grep patterns to find error definitions and handlers"
    }
  },
  "cross_cutting_risks": [
    {
      "type": "hotspot_with_failures|untested_failure_mode|cross_ownership_coupling|fragile_contract|exposed_endpoint|perf_regression_risk",
      "severity": "critical|high|medium|low",
      "description": "What the risk is",
      "involved_files": ["..."],
      "sources": ["which agents identified this"],
      "recommendation": "What to do"
    }
  ],
  "recommendations": [
    {
      "priority": "critical|high|medium|low",
      "category": "security|reliability|performance|testing|architecture|documentation",
      "description": "What should be done",
      "rationale": "Why, based on the analysis"
    }
  ]
}

Write valid JSON only. No prose.
```

---

### Phase 3: Artifact Generation

Read the synthesis:
```bash
cat {TARGET_PATH}/.claude-learning/synthesis.json
```

Generate the following four artifacts.

---

#### Artifact 0: Learning Metadata

Write `{TARGET_PATH}/.claude-learning-metadata.json`:
```json
{
  "service_name": "{SERVICE_NAME}",
  "target_path": "{TARGET_PATH}",
  "last_learned": "{ISO_TIMESTAMP}",
  "last_commit": "{CURRENT_GIT_COMMIT_SHA}",
  "learning_mode": "full|update",
  "agents_run": ["codebase-indexer", "dependency-mapper", "git-history-miner", "edge-failure-mapper", "security-mapper", "performance-analyzer", "test-fixtures-miner"],
  "findings_summary": {
    "total_files_analyzed": 0,
    "key_modules": ["..."],
    "primary_contributors": ["..."],
    "risk_areas": ["..."],
    "security_finding_count": 0,
    "test_coverage_assessment": "..."
  },
  "history": []
}
```

---

#### Artifact 1: CLAUDE.md

Create `{TARGET_PATH}/CLAUDE.md`:

```markdown
# {SERVICE_NAME}
> Auto-generated by /deep-learn on {current_date}
> Refresh: `/deep-learn {TARGET_PATH}` (full) | `/deep-learn {TARGET_PATH} --update` (incremental)

## Overview
{synthesis.summary}

---

## Institutional Knowledge

### Why This Code Is the Way It Is
{synthesis.tier1.decisions — key decisions with rationale}

### Known Gotchas
{synthesis.tier1.gotchas — things that will bite you, with context}

### Conventions
{synthesis.tier1.conventions — unwritten rules with file:line evidence}

### Implicit Contracts
{synthesis.tier1.implicit_contracts — what modules assume about each other}

### Engineer Notes
{synthesis.tier1.inline_knowledge — notable TODO/FIXME/HACK/NOTE comments}

---

## Architecture

### Module Index
| Module | Purpose | Entry Point |
|--------|---------|-------------|
{synthesis.tier2.module_index}

### API Surface
{synthesis.tier2.api_surface — routes/endpoints if applicable}

### Key Dependencies
{synthesis.tier2.dependency_graph — key internal and external}

### Ownership
{synthesis.tier2.ownership — who to talk to about what}

---

## Risk & Quality

### Security Findings
{synthesis.tier2.security_findings — severity-ranked}

### Failure Modes
{synthesis.tier2.risk_map — severity-ranked}

### Performance Hotspots
{synthesis.tier2.performance_hotspots — severity-ranked}

### Test Coverage
{synthesis.tier2.test_coverage — what's well-tested, what's not}
**Run tests:** `{test_run_command from test-fixtures-miner}`

### Cross-Cutting Risks
{synthesis.cross_cutting_risks — compound risks from multiple signals}

---

## Retrieval Guide
When you need current implementation details, retrieve them fresh:

| What You Need | How To Find It |
|---------------|----------------|
{synthesis.tier3.by_task}

### Per-Module Retrieval
{synthesis.tier3.by_module — for each module}

---

## Related Services
{cross-service.json — known and unknown dependencies}

---

## Recommendations
{synthesis.recommendations — priority-ranked}
```

---

#### Artifact 2: Named Project Skill

Create `~/.claude/commands/{SERVICE_NAME}.md`:

```markdown
# {SERVICE_NAME}
Quick-access expertise for the {SERVICE_NAME} codebase.

## Usage
```
/{SERVICE_NAME} <question or task>
```

---

## Instructions

### Step 0: Staleness Check (Always Do This First)

```bash
cat {TARGET_PATH}/.claude-learning-metadata.json 2>/dev/null
```

Extract `last_learned` and `last_commit`. Then:
```bash
git -C {TARGET_PATH} rev-list --count {LAST_COMMIT}..HEAD -- . 2>/dev/null
git -C {TARGET_PATH} log --oneline {LAST_COMMIT}..HEAD -- . 2>/dev/null | head -10
```

| Commits since learning | Action |
|---|---|
| 0 | Proceed with full confidence |
| 1–5 | Proceed, note recent changes |
| 6–20 | Warn user, suggest `--update` |
| 20+ | Strongly recommend refresh before proceeding |

---

You are an expert on **{SERVICE_NAME}** at `{TARGET_PATH}`.

## Tier 1: Institutional Knowledge

### What This Does
{synthesis.summary}

### Key Decisions
{synthesis.tier1.decisions}

### Gotchas — Read Before Making Changes
{synthesis.tier1.gotchas}

### Conventions — Follow These
{synthesis.tier1.conventions}

### Implicit Contracts — Don't Break These
{synthesis.tier1.implicit_contracts}

### Engineer Notes
{synthesis.tier1.inline_knowledge}

---

## Tier 2: Structural Map

### Module Index
| Module | Purpose | Entry Point | Key Exports |
|--------|---------|-------------|-------------|
{synthesis.tier2.module_index}

### API Surface
{synthesis.tier2.api_surface}

### Security Findings
| Location | Severity | Issue |
|----------|----------|-------|
{synthesis.tier2.security_findings — top findings}

### Failure Modes
| Location | Severity | Issue |
|----------|----------|-------|
{synthesis.tier2.risk_map — top failure modes}

### Performance Hotspots
| Location | Severity | Issue |
|----------|----------|-------|
{synthesis.tier2.performance_hotspots — top hotspots}

### Test Coverage
{synthesis.tier2.test_coverage}
**Run tests:** `{test_run_command}`

### Ownership
{synthesis.tier2.ownership}

### Cross-Cutting Risks
{synthesis.cross_cutting_risks}

---

## Tier 3: Retrieval Recipes — Use These for Current Code

Always retrieve implementation details fresh. Never guess from memory.

### By Task
| What You Need | How To Find It |
|---------------|----------------|
{synthesis.tier3.by_task}

### By Module
{synthesis.tier3.by_module}

---

## Related Services
{cross-service.json — known and unknown}

---

## How to Use This Expertise

**For exploration**: draw on Tier 1 and Tier 2. Use Tier 3 to show current code.

**For implementation**:
1. Check Tier 1 gotchas and conventions first
2. Use Tier 2 to find the right location
3. Retrieve current code with Tier 3 recipes
4. Flag relevant risks from the risk map and security findings

**For debugging**:
1. Check Tier 1 gotchas — was this a known issue?
2. Check Tier 2 risk map — is this a known failure mode?
3. Check Tier 2 dependency graph — is this a cascade?
4. Retrieve current error handling with Tier 3 recipes

**For code review**:
1. Verify Tier 1 conventions are followed
2. Verify Tier 1 implicit contracts aren't violated
3. Check Tier 2 security findings for patterns being introduced
4. Check test coverage for changed areas

---

## Refresh
```bash
# Incremental
/deep-learn {TARGET_PATH} --update

# Full refresh
/deep-learn {TARGET_PATH}
```
```

---

#### Artifact 3: Gitignore Update

```bash
if [ -f {TARGET_PATH}/.gitignore ]; then
  if ! grep -q '\.claude-learning/' {TARGET_PATH}/.gitignore 2>/dev/null; then
    printf '\n# Claude Code learning artifacts (machine-specific)\n.claude-learning/\n' \
      >> {TARGET_PATH}/.gitignore
  fi
else
  printf '# Claude Code learning artifacts (machine-specific)\n.claude-learning/\n' \
    > {TARGET_PATH}/.gitignore
fi
```

---

#### Artifact 4: Service Registry Update

```bash
cat ~/.claude/learned-services-registry.json 2>/dev/null \
  || echo '{"version":"1.0","services":{},"dependency_graph":{"edges":[]}}'
```

Add/update this service's entry using synthesis data. Add dependency edges from `cross-service.json`. Write back to `~/.claude/learned-services-registry.json`.

---

### Phase 4: Summary Report

```
## Deep Learn Complete: {SERVICE_NAME}

**Path:** {TARGET_PATH}
**Mode:** Full analysis
**Commit:** {CURRENT_COMMIT_SHA}

### Artifacts Created
1. **CLAUDE.md** → `{TARGET_PATH}/CLAUDE.md` (auto-loads in this directory)
2. **Skill: /{SERVICE_NAME}** → `~/.claude/commands/{SERVICE_NAME}.md` (available everywhere)
3. **Learning index** → `{TARGET_PATH}/.claude-learning/` (gitignored)
4. **Metadata** → `{TARGET_PATH}/.claude-learning-metadata.json`

### Knowledge Captured
**Tier 1 — Institutional:**
- N architectural decisions
- N gotchas
- N conventions
- N implicit contracts
- N engineer notes (TODO/FIXME/etc.)

**Tier 2 — Structural:**
- N modules indexed
- N API endpoints mapped
- N failure modes identified
- N security findings (X critical/high)
- N performance hotspots
- Test coverage: {assessment}

**Tier 3 — Retrieval Recipes:**
- N per-module retrieval patterns
- N task-based retrieval patterns

### Top Risks
{Top 3 cross_cutting_risks from synthesis}

### Recommendations
{Top 3 recommendations from synthesis}

---
*Use: `/{SERVICE_NAME}` | Update: `/deep-learn {TARGET_PATH} --update`*
```

---

## Error Handling

- Target path doesn't exist → stop immediately with clear error
- Any agent fails → continue with remaining agents, note the gap in synthesis
- Git history unavailable → skip git-history-miner, note limitation
- `CLAUDE.md` already exists → ask user: overwrite or merge?
- Skill with same name already exists → ask user: overwrite?
- `--update` with no metadata → fall back to full mode with notification
- Metadata file corrupted → back it up, start fresh
- Synthesis file exceeds 100KB → warn that the codebase may benefit from splitting into smaller service scopes

## Notes

- Full mode uses Opus-class agents for deep analysis. Expect meaningful processing time.
- Update mode is significantly faster — only touches changed areas.
- `.claude-learning/` is gitignored by default — each developer generates their own index.
- `CLAUDE.md` and `.claude-learning-metadata.json` are intended to be committed and shared.
- The generated `/{SERVICE_NAME}` skill is immediately available everywhere after creation.
- Tier 3 retrieval recipes are always executed fresh — they are grep/glob commands, not cached facts. This is intentional.
