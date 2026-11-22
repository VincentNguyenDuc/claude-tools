---
id: layout-store
title: Save node positions in .claude-dag/layout.json
kind: task
status: done
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
- New `src/claude_dag/layout.py`: `read_layout` (drops malformed entries and unknown ids, and returns `{}` for a missing or corrupt file), `save_layout` (merge by default, where `null` removes an id; `replace=True` replaces everything; ids that aren't nodes are dropped; bad points are a 400), `rename_in_layout` and `drop_from_layout`, plus `layout_version`. The file is written with `_atomic_write`, and coordinates are rounded to 0.1.
- `graph.py`: `update(id=...)` moves the position entry and `remove` deletes it. Both do nothing if the file is missing or corrupt.
- `server.py`: `GET /api/layout` → `{positions, version}`. `PUT /api/layout` takes `{positions, replace?}` and goes through the same Host/Origin/JSON checks and the write lock. `GET /api/version` now also returns `layout`.
- **Version decision:** layout has its own version (mtime+size of layout.json, `"0"` when it doesn't exist). `dir_version` only hashes `nodes/*.md`, so a drag doesn't trigger a graph reload.
- README Files section lists `layout.json`. It's meant to be committed, like the nodes.

Evidence: `tests/test_layout.py` has 6 tests: round trip/merge/replace/null delete, validation plus unknown ids, unknown ids dropped on read, rename/remove, 4 kinds of corrupt file plus a missing file, and Origin/Host/non-JSON rejection. The full suite is 42 passed.

Caveat: the UI doesn't read the layout yet. `node-drag` will need to use `GET /api/layout` and fall back to automatic layout for nodes with no saved position.
