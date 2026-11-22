---
id: safe-edits
title: Conflict-safe saving from the edit panel
kind: task
status: done
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
- `model.py`: `Node.revision()` is a sha1 of the canonical markdown, so a formatting-only hand edit doesn't count as a conflict. `Graph.to_json` nodes and the server's POST/PATCH responses now include `rev`. MCP/CLI output is unchanged.
- `server.py`: `PATCH /api/nodes/<id>` takes an optional `base_rev`. If it doesn't match, the server returns 409 `{error, node}` with the current node and its `rev`. Without `base_rev` the last writer wins, as before. The check runs under the write lock.
- `index.html`: `fillForm` records `base = {rev, node, form}`. Save sends only the fields that differ from what the form was filled with, plus `base_rev`, and sends nothing if nothing changed. A 409 opens a `#conflict` box listing the fields that changed on disk (Notes is shown as "(edited)"), with **Reload (discard mine)**, which refills from disk, and **Overwrite**, which resends only my changed fields based on the disk `rev`. Edits on disk to other fields survive. `api()` errors now carry `status` and `data`. The poll banner text is updated.
- Tests: `test_server.py::test_patch_base_rev` covers matching (200), stale (409 with node, nothing written), retry with the new rev (200, keeps the other edit) and no rev (200). `test_ui.py` adds three tests: only `{body, base_rev}` is sent; overwrite keeps the disk `status: done` and writes my body; reload discards mine. The full suite is 46 passed, and the UI tests passed 3 runs in a row.

Note: the `page` fixture ignores "Failed to load resource" console lines, which the browser logs for expected 4xx responses.
