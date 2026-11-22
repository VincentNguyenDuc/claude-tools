---
id: node-search
title: Search nodes by title or id
kind: task
status: todo
deps: [ui-test-harness]
milestone: m4-ui-readable
verify: cd plugins/dag && uv run -q --group dev pytest -q tests/test_ui.py -k search
---

## Goal / acceptance

- `/` (or ⌘K) opens a search box that matches titles and ids as you type, case-insensitively.
- Enter centres the view on the match and selects it. Esc closes the box.
- A match hidden by the current filter clears that filter so the node can be shown.

## Notes

## Result
