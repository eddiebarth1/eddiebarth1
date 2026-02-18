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
| `/deep-learn` | Full codebase intelligence pass - structure, flows, abstractions, entry points |
| `/git-archaeology` | Mine git history for patterns, hotspots, team conventions, evolution |
| `/dep-audit` | Map dependency graph, flag vulnerabilities, identify drift |
| `/security-scan` | OWASP Top 10 + secrets + auth/authz + injection analysis with proposed fixes |
| `/arch-map` | Generate architectural understanding - layers, boundaries, data flows |
| `/pattern-extract` | Derive team coding conventions, error handling patterns, testing style |
| `/debt-radar` | Detect tech debt, complexity hotspots, stale code, and risky abstractions |
| `/onboard` | Generate a developer onboarding guide from codebase analysis |
| `/perf-audit` | Identify performance bottlenecks, memory patterns, and inefficient operations |
| `/review-pr` | Context-aware PR review using deep codebase knowledge |

## Recommended Workflow for a New Codebase

1. `/deep-learn` - Get the lay of the land
2. `/git-archaeology` - Understand how it evolved and who made what decisions
3. `/arch-map` - Lock in the architectural mental model
4. `/pattern-extract` - Know the team's conventions before writing a line
5. `/security-scan` - Know the risk surface before you ship anything
6. `/dep-audit` - Understand what you're depending on and where the vulnerabilities are

After that foundation: use `/debt-radar`, `/perf-audit`, and `/review-pr` continuously as you develop.

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
