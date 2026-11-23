---
id: m5-yaml-storage
title: 'M5: plan stored in YAML, UI read-only'
kind: milestone
status: todo
deps: [m4-ui-readable]
---

## Goal / acceptance

- The plan's structure (ids, titles, kind, status, deps, milestones, verify) lives in hand-editable YAML files under `.claude-dag/plan/`, which may reference each other. Nesting expresses deps and membership, and `after:` adds extra deps, across files too.
- Node text lives in separate markdown files that a node points to with a `body:` field.
- The MCP tools and CLI read and write this format, and keep comments and layout intact. The web UI is a read-only view: it shows the plan, can be dragged to arrange it, and links to the source files.
- This repo's own plan is migrated with nothing lost. Released as dag 0.5.0.

## Notes

Comes from discussion on 2026-11-22, after `ui-feedback`. It comes before activity tracking (M6) and VS Code (M7) so those are built on the new storage rather than reworked.
Editing in the UI (from M3) goes away. The plan is edited in the YAML and markdown files, by hand or by Claude through the tools. Dragging stays, because positions are view state stored in `layout.json`.

## Result
