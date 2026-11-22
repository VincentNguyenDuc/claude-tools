---
id: node-labels
title: Wrap node titles instead of truncating
kind: task
status: todo
deps: [ui-test-harness, node-drag]
milestone: m4-ui-readable
verify: cd plugins/dag && uv run -q --group dev pytest -q tests/test_ui.py -k labels
---

## Goal / acceptance

- Titles wrap to up to two lines and are cut with an ellipsis only after that. The node height adapts and the layout spacing accounts for it.
- The id and status line is never truncated for ids up to 30 characters.
- The full title is still available as a hover tooltip.

## Notes

Currently `clip(title, 27)` with fixed `NW=210, NH=52` (`index.html`).

## Result
