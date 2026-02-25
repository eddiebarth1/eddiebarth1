Perform a deep archaeological analysis of this repository's git history. Your goal is to surface the patterns, decisions, evolution, and risk signals that live in the commit log - things that aren't visible from reading the code alone.

## Context Bootstrap

Before starting, check whether `/deep-learn` has already been run on this codebase:

```bash
cat .claude-learning-metadata.json 2>/dev/null
cat .claude-learning/manifest.json 2>/dev/null
cat .claude-learning/git-history-miner.json 2>/dev/null
```

**If git-history-miner.json exists**: Prior institutional knowledge has been captured. Load it and use it as a baseline — note `decisions`, `gotchas`, `hotspots`, and `contributors` that were already found. In your analysis, focus on:
- Extending the decision log (look for commits since `_last_incremental_update` if present)
- Finding evolution patterns not yet captured
- Validating or updating the ownership map
- Surfacing any reverts or recurring fixes in recent history that post-date the last analysis

**If manifest.json exists**: Use `top_level_modules` to scope per-module contributor analysis (Phase 5) without having to discover the module structure first.

**If no context exists**: Proceed with the phases below, doing full discovery.

## Phase 1: Repository Vitals

Run the following and analyze the output:

```bash
# Repository age and total commits
git log --oneline | wc -l
git log --format="%ad" --date=short | tail -1

# Contributors
git shortlog -sn --all | head -20

# Commit frequency over time (activity heatmap)
git log --format="%ad" --date=format:"%Y-%m" | sort | uniq -c | sort -k2

# Branch topology
git log --oneline --graph --all --decorate | head -50
```

## Phase 2: Hotspot Analysis

Find the files that change most frequently - these are your highest-risk files, your core business logic, and your most likely sources of bugs:

```bash
# Top 20 most-changed files
git log --name-only --format="" | grep -v "^$" | sort | uniq -c | sort -rn | head -20

# Files changed in the last 30 days
git log --since="30 days ago" --name-only --format="" | grep -v "^$" | sort | uniq -c | sort -rn | head -20

# Files with most contributors (high coordination overhead)
git log --format="%H" | xargs -I{} git show --name-only --format="" {} 2>/dev/null | grep -v "^$" | sort | uniq -c | sort -rn | head -20
```

## Phase 3: Commit Message Pattern Analysis

Analyze the language of commit messages to understand team culture and recurring issues:

```bash
# Full commit log for analysis
git log --format="%s" --all | head -200

# Look for fix/bug patterns (indicates recurring problem areas)
git log --format="%s" --all | grep -iE "(fix|bug|patch|revert|hotfix)" | head -50

# Look for feature/refactor patterns
git log --format="%s" --all | grep -iE "(feat|add|refactor|improve|update)" | head -50

# Revert commits (indicates problematic changes)
git log --format="%s %H" --all | grep -i revert | head -20
```

## Phase 4: Evolution Analysis

Understand how the codebase has changed over time:

```bash
# Major structural changes (large diffs)
git log --format="%H %s" --all | head -100

# When was each major directory last touched?
for dir in */; do echo "$dir: $(git log -1 --format="%ar by %an" -- "$dir")"; done

# Recent large commits (potential big-bang changes)
git log --format="%H %s" --all | head -50 | while read hash msg; do
  lines=$(git show --stat "$hash" 2>/dev/null | tail -1)
  echo "$lines | $msg"
done | sort -rn | head -20
```

## Phase 5: Team Pattern Analysis

Read 50+ recent commit messages and the diffs of the 10 most significant recent commits. From this, derive:

1. **Commit conventions**: Do they follow conventional commits? What format do they use?
2. **PR/review culture**: Are commits squashed? Merge commits or rebases?
3. **Release patterns**: How are releases tagged and versioned?
4. **Recurring themes**: What keeps coming up? Auth issues? Performance? A specific module that always breaks?
5. **Risk areas**: Which files have the most churn + most contributors? That combination is a bug magnet.

## Phase 6: Synthesis

Produce a structured report:

**Repository Timeline**: When did it start, major phases of development, current velocity.

**Hotspot Map**: Top 10 highest-risk files with churn counts and why they matter.

**Team Patterns**: How this team commits, reviews, and releases.

**Recurring Problems**: What keeps breaking or getting re-fixed.

**Evolution Story**: How has the architecture changed? What got abandoned? What got rewritten?

**Risk Signals**: Specific findings that warrant closer inspection (reverts, hotfixes, files with single-author ownership, etc.).

**Recommendations**: Based on the history, what should the team do differently or pay more attention to?

$ARGUMENTS
