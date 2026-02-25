# Compound Engineering System

This repository is a compound engineering toolkit - a collection of Claude Code agents and slash commands designed to let a small team move with the leverage of a much larger one. Each command is built to derive deep context, surface non-obvious patterns, and compound that understanding across every project you touch.

## Philosophy

**Compound engineering** means every interaction builds on prior knowledge. Agents don't just answer questions - they learn the shape of a codebase, its history, its team conventions, and its failure modes. That accumulated context is what separates a 10x output from a well-prompted chatbot.

Key principles:
- **Depth over breadth**: Go beyond surface-level file reads. Mine git history, trace data flows, map dependency trees to their leaves.
- **Pattern recognition**: Codebases have personalities - naming conventions, preferred abstractions, recurring anti-patterns. Surface them explicitly.
- **Defensive posture**: Assume every codebase has security debt. Flag it. Propose fixes. Don't wait to be asked.
- **Compounding context**: When you learn something in one command, reference it in the next. Build a mental model, not a series of isolated answers.

## Available Commands

| Command | Purpose |
|---|---|
| `/deep-learn` | Full pipeline: 7 parallel agents → synthesis → generates `CLAUDE.md` + a named project skill. Supports `--update` for incremental refresh. |
| `/git-archaeology` | Deep dive into git history — decisions, evolution, ownership, recurring problems |
| `/dep-audit` | Map dependency graph, flag vulnerabilities, identify drift and license risk |
| `/security-scan` | OWASP Top 10 + secrets + auth/authz + injection analysis with proposed fixes |
| `/arch-map` | Architectural map — layers, boundaries, data flows, system context |
| `/pattern-extract` | Derive team coding conventions, error handling patterns, testing style |
| `/debt-radar` | Detect tech debt, complexity hotspots, stale code, and risky abstractions |
| `/onboard` | Generate a developer onboarding guide from codebase analysis |
| `/perf-audit` | Identify performance bottlenecks, N+1 queries, memory patterns, async issues |
| `/review-pr` | Context-aware PR review using deep codebase knowledge |

## How `/deep-learn` Works

`/deep-learn` is the entry point for a new codebase. It orchestrates 7 specialized parallel agents:

| Agent | Focus |
|---|---|
| `codebase-indexer` | Structure, modules, entry points, conventions |
| `dependency-mapper` | Import graph, API surface, coupling hotspots |
| `git-history-miner` | Institutional knowledge — decisions, gotchas, ownership |
| `edge-failure-mapper` | Error handling, failure modes, validation gaps |
| `security-mapper` | Auth, injection surfaces, secrets, crypto |
| `performance-analyzer` | N+1 queries, blocking I/O, caching gaps |
| `test-fixtures-miner` | Test infrastructure, coverage assessment |

Each agent writes structured JSON to `.claude-learning/`. A synthesis agent then cross-references them to find compound risks (e.g. high-churn files with unhandled errors). The final output is:

1. **`.claude-learning/`** — Structured JSON index (gitignored, machine-specific)
2. **`CLAUDE.md`** — Tiered knowledge doc that auto-loads in this directory
3. **`~/.claude/commands/{project-name}.md`** — Named skill, available everywhere

### Tiered Knowledge Architecture

| Tier | What It Contains | How It's Used |
|---|---|---|
| **Tier 1 — Institutional** | Decisions, gotchas, conventions, implicit contracts | Written in full — this is the knowledge you can't retrieve with grep |
| **Tier 2 — Structural** | Module index, API surface, risk map, ownership | Reference when navigating or designing changes |
| **Tier 3 — Retrieval Recipes** | Grep/glob/git commands per module and task | Always executed fresh — never used as cached facts |

### Incremental Updates

After the initial run, use `--update` for fast incremental refresh:
```bash
/deep-learn . --update        # only re-runs agents for changed areas
/deep-learn . --update --force  # forces refresh even if no changes detected
```

## Recommended Workflow for a New Codebase

1. `/deep-learn .` — Full intelligence pass. Creates `CLAUDE.md` + named project skill. Takes time; worth it.
2. `/{project-name}` — Use the generated skill for all subsequent work in this codebase
3. `/deep-learn . --update` — Run after significant changes to keep knowledge current

The other commands become **targeted deep dives** after `/deep-learn` — they're manifest-aware and will use existing `.claude-learning/` context to scope their work:

- `/security-scan` — Extends `security-mapper.json` with a full OWASP pass
- `/perf-audit` — Extends `performance-analyzer.json` with deeper analysis
- `/dep-audit` — Extends `dependency-mapper.json` with version/CVE/license assessment
- `/git-archaeology` — Extends `git-history-miner.json` with narrative analysis
- `/arch-map` — Extends `codebase-indexer.json` + `dependency-mapper.json` into a full architectural document
- `/pattern-extract` — Extends `codebase-indexer.conventions` into a full style guide
- `/debt-radar` — Cross-references `edge-failure-mapper.json` + `git-history-miner.json` hotspots
- `/onboard` — Uses the full synthesis to generate a new-engineer guide
- `/review-pr` — Uses `synthesis.json` for context-aware review against known patterns and risks

## Using These Commands Globally

These commands live in this repo but can be symlinked or referenced from any project. To use them globally:

```bash
# Option 1: Symlink .claude into any project
ln -s /path/to/this/repo/.claude /path/to/your-project/.claude

# Option 2: Copy just the commands directory
cp -r /path/to/this/repo/.claude/commands /path/to/your-project/.claude/commands

# Option 3: Set CLAUDE_CONFIG_DIR to point here
export CLAUDE_CONFIG_DIR=/path/to/this/repo/.claude
```

## Notes for the Agent

When executing any command in this system:
- Always read broadly before concluding. A single file is never the whole story.
- Git history is first-class evidence. Use it.
- When you find a pattern, name it. Unnamed patterns go unnoticed.
- When you find a vulnerability, don't just flag it - explain the attack vector and propose a concrete fix.
- Structure output for scanning: use headers, tables, and code blocks. Dense prose gets skipped.
- **Use retrieval-first**: Targeted grep/glob over bulk file reads. Use the manifest scope boundaries to avoid wasted work.
- **Tier 3 recipes are commands, not facts**: Always execute retrieval recipes fresh rather than answering from memory.
- **Context compounds**: When `.claude-learning/` exists, build on it. Don't repeat analysis that's already been done well.

## Artifact Locations

| Artifact | Location | Committed? |
|---|---|---|
| Learning index | `{project}/.claude-learning/` | No (gitignored, machine-specific) |
| Metadata | `{project}/.claude-learning-metadata.json` | Yes (shared) |
| Project CLAUDE.md | `{project}/CLAUDE.md` | Yes (shared) |
| Named project skill | `~/.claude/commands/{name}.md` | No (global, per-developer) |
| Service registry | `~/.claude/learned-services-registry.json` | No (global, per-developer) |
