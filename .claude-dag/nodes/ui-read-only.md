---
id: ui-read-only
title: Make the web UI a read-only view
kind: task
status: todo
deps: [yaml-backend]
milestone: m5-yaml-storage
verify: cd plugins/dag && uv run -q --group dev pytest -q tests/test_ui.py tests/test_server.py
---

## Goal / acceptance

- The server's plan-editing endpoints and the UI's edit controls (status, fields, body editing, add, link) are removed. Layout endpoints and dragging stay.
- The node panel shows the source `file:line` and the body file(s) as links that open in the editor (e.g. `vscode://file/<path>:<line>`).
- Tests that covered UI editing are removed or rewritten to check that it's gone. Preview, search, trace and labels tests still pass.

## Notes

## Result
