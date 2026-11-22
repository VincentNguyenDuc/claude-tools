---
id: safe-edits
title: Conflict-safe saving from the edit panel
kind: task
status: todo
deps: []
milestone: m3-ui-arrange
verify: cd plugins/dag && uv run -q --group dev pytest -q tests/test_server.py
---

## Goal / acceptance

- The panel sends only the fields the user actually changed.
- `PATCH /api/nodes/<id>` accepts a base revision of the node (for example a hash of the file content when the panel was opened). It returns 409 with the current node if the file has changed since.
- On a 409 the UI shows what changed on disk and offers "Reload (discard mine)" or "Overwrite". It never overwrites silently.
- Requests without a base revision still work, so the CLI and MCP tools keep their current behaviour.
- Server tests cover a matching revision (200), a stale revision (409) and a missing revision (200).

## Notes

Today the panel sends every field and the server applies them, so the last writer wins. Example: Claude sets `status: done` while you edit the notes, you press Save, and the status goes back to the old value. The 1.5 s poll only shows a banner.

## Result
