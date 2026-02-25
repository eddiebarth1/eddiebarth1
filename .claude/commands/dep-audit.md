Perform a comprehensive dependency audit of this codebase. Map every external dependency, assess the risk each one carries, identify vulnerabilities, and surface opportunities to simplify or upgrade.

## Context Bootstrap

Before starting, check whether `/deep-learn` has already been run on this codebase:

```bash
cat .claude-learning-metadata.json 2>/dev/null
cat .claude-learning/manifest.json 2>/dev/null
cat .claude-learning/dependency-mapper.json 2>/dev/null
```

**If manifest.json exists**: Use `external_dependencies` for the initial package list and `package_manager` to know which lockfile and audit tool to reach for. Use `scope_boundaries.vendor` to identify vendored code that should be audited separately.

**If dependency-mapper.json exists**: Use `external_deps` as your starting inventory — it already maps each package to the files that use it and describes its purpose. Focus your analysis on assessing risk, versions, and vulnerabilities rather than re-discovering what's used. Use `external_services` to understand runtime dependencies beyond the package manifest.

**If no context exists**: Proceed with the phases below, doing full discovery.

## Phase 1: Dependency Inventory

Identify all dependency manifests in the project:
- `package.json` / `package-lock.json` / `yarn.lock` / `pnpm-lock.yaml` (Node.js)
- `go.mod` / `go.sum` (Go)
- `Cargo.toml` / `Cargo.lock` (Rust)
- `requirements.txt` / `pyproject.toml` / `Pipfile` / `poetry.lock` (Python)
- `Gemfile` / `Gemfile.lock` (Ruby)
- `pom.xml` / `build.gradle` (Java/Kotlin)
- Any vendored directories (`vendor/`, `_vendor/`, `third_party/`)

Read each manifest and catalog:
1. Total number of direct dependencies
2. Total number of transitive dependencies (from lockfiles)
3. Production vs. development dependencies
4. Dependencies pinned to exact versions vs. ranges

## Phase 2: Vulnerability Surface

For each package manager found, note which vulnerability tools can be run:
- Node.js: `npm audit`, `yarn audit`, or `pnpm audit`
- Python: `pip-audit`, `safety`
- Go: `govulncheck`
- Rust: `cargo audit`
- Ruby: `bundler-audit`

If any of these tools are available, run them and include the output. If not, note what should be installed.

Then manually assess risk by examining:

```bash
# Node.js - check for known patterns
cat package.json | grep -E '"(version|dependencies|devDependencies)"' -A 100

# Go - check for replace directives and indirect deps
cat go.mod

# Python
cat requirements.txt pyproject.toml 2>/dev/null
```

## Phase 3: Dependency Health Assessment

For each direct dependency, assess:

**Maintenance health signals** (read the lockfile/manifest and reason about each):
1. Is this package still actively maintained?
2. Is this a well-known, widely-used package or an obscure one?
3. Is the version pinned to something very old?
4. Is there a newer major version that might have breaking changes to plan for?

**Risk classification**:
- **Critical path**: Used in authentication, payments, data handling, or core business logic
- **High surface area**: Used everywhere in the codebase
- **Low risk**: Dev tools, build tooling, type definitions

## Phase 4: Dependency Usage Analysis

For the 10 most significant dependencies, trace how they're actually used:

```bash
# Find all imports of a specific package
grep -r "require\|import\|from" --include="*.js" --include="*.ts" --include="*.py" --include="*.go" . | grep -v "node_modules\|vendor" | grep "<package-name>"
```

Answer for each:
1. Is this dependency used in 1 file or 50?
2. Could it be replaced with a standard library function?
3. Is only a small part of a large library being used?

## Phase 5: License Analysis

Identify the licenses of all direct dependencies. Flag any:
- GPL/AGPL licenses (may require open-sourcing your code)
- Unlicensed packages
- Non-commercial-only licenses
- License conflicts

## Phase 6: Synthesis

Produce a structured report:

**Dependency Summary Table**:
| Name | Version | Type | Last Updated | License | Risk Level | Notes |

**Vulnerability Findings**: Any known CVEs or audit findings with severity and remediation steps.

**Outdated Dependencies**: Packages significantly behind latest, with upgrade path notes.

**Unused or Redundant Dependencies**: Packages that appear in the manifest but may not be needed.

**License Risks**: Any licensing concerns.

**Simplification Opportunities**: Places where a dependency could be dropped for a stdlib solution.

**Recommended Actions**: Prioritized list of what to fix, upgrade, or remove.

$ARGUMENTS
