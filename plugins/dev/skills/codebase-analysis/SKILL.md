---
name: codebase-analysis
description: Explore a codebase and write a standalone knowledge document (architecture, features, data flow, gotchas, glossary) that a future engineer or LLM session can use to change it safely. Use when asked for a codebase analysis, brain dump, architecture overview or onboarding doc, or "/dev:codebase-analysis [name]".
argument-hint: "[codebase-name] (defaults to the repo directory name)"
---

Write a master knowledge document for this codebase. It's deeper than CLAUDE.md: CLAUDE.md holds rules for working in the repo, this document explains how the system works.

## Output

- `<name>` = the argument, else the repo directory name.
- Main document: `docs/codebase-analysis/<name>/CODEBASE_KNOWLEDGE.md`. Supporting diagrams or schemas: `docs/codebase-analysis/<name>/assets/`.
- If the document already exists, update it rather than starting over, and keep sections that are still accurate.
- All file references are paths relative to the repo root, with line numbers where useful (`src/x.py:42`).

## How to explore

- Map before reading: the file tree, build and config files, entry points, then the most connected modules. Tests (especially end-to-end ones) are a quick way to find features.
- Read what you need, not everything. Skip vendored code, generated files and build output; note them as such.
- For a large repo, split the exploration by area. Use subagents only if the user asked for them.
- Never guess. If something can't be confirmed from the code, list it under Open questions with your best reading and a confidence level.

## Document structure

1. **Overview.** What the system is, who uses it, the tech stack, the architecture style, and how to build, run and test it.
2. **Architecture.** Major components and how they interact, data flow from input to storage to output, external integrations, and cross-cutting concerns (auth, config, logging, error handling, concurrency). Include Mermaid diagrams (`graph TD`, `sequenceDiagram`, `erDiagram`), each small and focused.
3. **Features.** For each feature: purpose, entry points, the modules and functions involved, data touched, side effects, interactions with other features, and edge cases.
4. **Things to know before changing code.** Non-obvious design decisions and their likely reasons, invariants, performance-sensitive paths, security-relevant code, hard-coded business rules, and traps.
5. **Reference.** Glossary of domain terms; key modules, classes and functions with one-line summaries; data schemas; internal and external APIs with examples.
6. **Open questions and assumptions.**

Write plainly and specifically: every claim should point to a file, function or test. A reader without access to the repo should still understand the system.

Finish by giving the document path and a short summary of the most important findings.
