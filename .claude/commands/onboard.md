Generate a comprehensive onboarding guide for a new developer joining this project. The guide should be derived entirely from reading the codebase, git history, and configuration - not generic advice. When you're done, a new engineer should be able to get the project running, understand what they're looking at, and make a confident first contribution.

## Phase 1: Project Context

Read everything that gives project-level context:
1. README, CONTRIBUTING, DEVELOPMENT, ARCHITECTURE docs
2. Package manifests (package.json, go.mod, etc.) for description and scripts
3. CI/CD configuration (.github/workflows, .circleci, Jenkinsfile, etc.)
4. Docker and docker-compose files
5. Makefile or task runner configs

Then answer:
- What does this project do?
- Who uses it?
- Where does it fit in a larger system?

## Phase 2: Local Development Setup

Derive the exact commands needed to:

1. **Prerequisites**: What needs to be installed first? (Node, Go, Python, Docker, databases, etc.)

```bash
# Check for tooling requirements
cat .nvmrc .node-version .python-version .go-version 2>/dev/null
cat README* CONTRIBUTING* DEVELOPMENT* 2>/dev/null | head -100
```

2. **Clone and configure**: Any post-clone setup (env files, config, etc.)

```bash
# Look for setup scripts and env templates
find . -name "setup*" -o -name ".env.example" -o -name ".env.template" -o -name "*.sample" 2>/dev/null \
  | grep -v ".git\|node_modules\|vendor"
```

3. **Install dependencies**: The exact commands

4. **Database/infrastructure setup**: Any services that need to run locally

5. **Run the application**: The exact command to start it

6. **Run the tests**: The exact command(s) to run the full test suite

Document each step with the actual command and what to expect when it succeeds.

## Phase 3: Codebase Tour

Give a guided tour of the most important parts of the codebase. For each area:
- What directory/file is it in?
- What does it do?
- Why does it matter?
- What should a new engineer understand about it before touching it?

Focus on:
1. Entry points (where execution begins)
2. Core business logic (the most important 20% of the code)
3. Data layer (how data is stored and retrieved)
4. API surface (how the world interacts with this system)
5. Configuration (how the system is configured)

## Phase 4: Key Concepts Glossary

Read the domain model, types, and comments to extract domain-specific terms. Define:
- Project-specific terminology that isn't obvious
- Internal names for concepts (e.g., "a Widget is what we call...")
- Acronyms used in the codebase

## Phase 5: Development Workflow

From the git history and CI configuration, derive:

1. **Branching strategy**: How are branches named? (feature/, fix/, etc.)
2. **Commit conventions**: What does a good commit message look like here?
3. **PR process**: What does the CI check? What's required to merge?
4. **Code review culture**: From commit messages and PR patterns, what do reviewers focus on?

```bash
# Derive branching and commit conventions from history
git log --format="%s" --all | head -30
git log --format="%D" --all | grep -v "^$" | head -20
cat .github/pull_request_template.md 2>/dev/null
cat CONTRIBUTING* 2>/dev/null
```

## Phase 6: Common Tasks

Document how to do the 5 most common development tasks in this codebase. Based on the project type, these might include:
- Adding a new API endpoint
- Adding a new database migration
- Adding a new feature flag
- Writing a test for a new function
- Adding a new dependency

For each, give the specific files to create/modify and the pattern to follow.

## Phase 7: Gotchas and Tribal Knowledge

From code comments, git history commit messages, and code patterns, surface:
1. Non-obvious things that trip up new developers
2. "Never do X because..." patterns
3. Configuration that must be set for things to work
4. Known issues or workarounds that are in the code
5. Parts of the codebase that are under active change and should be approached carefully

```bash
# Find warning comments and important notes
grep -rn --include="*.js" --include="*.ts" --include="*.go" --include="*.py" \
  -E "(IMPORTANT|WARNING|CAUTION|NOTE|DANGER|DO NOT|NEVER|ALWAYS|HACK)" . \
  | grep -v "node_modules\|vendor\|.git" | head -30
```

## Phase 8: Synthesis

Produce a complete onboarding document with these sections:

1. **Welcome** - What this is and why it exists
2. **Prerequisites** - What to install before starting
3. **Setup** - Step-by-step with exact commands
4. **First Run** - How to verify everything works
5. **Codebase Tour** - The 10 most important files/directories and what they do
6. **Key Concepts** - Domain glossary
7. **Development Workflow** - How to work here day-to-day
8. **Common Tasks** - Recipes for frequent operations
9. **Gotchas** - What to know that isn't written down anywhere
10. **Who to Ask** - (Note: derived from git history - who commits to which areas)

$ARGUMENTS
