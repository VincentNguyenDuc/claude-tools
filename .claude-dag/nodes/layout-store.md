---
id: layout-store
title: Save node positions in .claude-dag/layout.json
kind: task
status: todo
deps: []
milestone: m3-ui-arrange
verify: cd plugins/dag && uv run -q --group dev pytest -q tests/test_layout.py
---

## Goal / acceptance

- `GET /api/layout` returns `{positions: {id: {x, y}}, version}`. `PUT /api/layout` replaces or merges positions and is written atomically.
- Positions for unknown ids are dropped on read. Renaming a node through `Graph.update` moves its entry, and removing a node deletes it.
- `layout.json` is optional: if it's missing or corrupt, the UI falls back to automatic layout and doesn't error.
- The existing localhost, JSON-only and Origin checks also apply to `PUT`.
- Tests cover the round trip, rename, remove and a corrupt file.

## Notes

Decision: positions go in one `layout.json` per `.claude-dag/`, not in node frontmatter. Reasons: a drag shouldn't change node files (git diff noise, and it would wake Claude's file-change detection), and node files stay about the work itself.
Rejected alternatives: frontmatter `pos:` in `extra`, and browser localStorage (not shared, easily lost).

Decide whether `layout.json` bumps `dir_version`. Probably it should use a separate version, so that dragging doesn't make the UI reload the whole graph.

## Result
