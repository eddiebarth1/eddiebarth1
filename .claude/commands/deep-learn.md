Perform a comprehensive deep-learning pass on the codebase. Your goal is to build a complete mental model of this project that would let you work on it as fluently as its original authors. Do not skim - go deep.

## Phase 1: Structural Orientation

1. Identify the project type (web app, CLI, library, service, monorepo, etc.)
2. Map the top-level directory structure and explain the purpose of each major directory
3. Identify the primary language(s) and runtime versions
4. Find all configuration files (package.json, go.mod, Cargo.toml, pyproject.toml, Makefile, Dockerfile, docker-compose, CI configs, etc.) and summarize what each one tells you about how the project is built and run
5. Identify the entry points - where does execution begin? Where does the application start?

## Phase 2: Core Abstractions

6. Identify the 5-10 most important files in the codebase - the ones without which nothing works
7. For each important file, explain: what it does, what it depends on, and what depends on it
8. Find the primary data models / domain types. Read them and explain what they represent in business terms
9. Map the primary interfaces and abstractions - what are the key contracts this codebase relies on?
10. Identify any frameworks or architectural patterns in use (MVC, hexagonal, CQRS, event-driven, etc.)

## Phase 3: Data Flows

11. Trace at least one complete request/operation from entry point to output - follow the data all the way through
12. Identify how state is managed (database, in-memory, external cache, etc.)
13. Find all external integrations - APIs called, queues consumed, events emitted
14. Map where data is persisted and what the schema looks like

## Phase 4: Build, Test, and Operations

15. Understand the build process - how is the project compiled/bundled?
16. Understand the test structure - what kinds of tests exist, where they live, how to run them
17. Find the deployment configuration - how does this run in production?
18. Identify environment variables, feature flags, and configuration injection points

## Phase 5: Synthesis

Produce a structured summary with these sections:

**Project Identity**: One paragraph describing what this is and what it does.

**Architecture**: How the pieces fit together.

**Key Abstractions**: The 5-10 concepts you must understand to work here.

**Data Flow**: The path data takes through the system.

**Critical Files**: The files you must not break.

**Build & Run**: Exactly how to build, test, and run this locally.

**Unknowns & Gaps**: Things you couldn't determine from the code alone - questions to ask the team.

$ARGUMENTS
