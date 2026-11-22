---
id: milestone-groups
title: Draw a box around each milestone's members
kind: task
status: todo
deps: [ui-test-harness, node-drag]
milestone: m4-ui-readable
verify: cd plugins/dag && uv run -q --group dev pytest -q tests/test_ui.py -k groups
---

## Goal / acceptance

- Each milestone gets a tinted, labelled rectangle behind its member nodes that follows pinned and dragged positions.
- Overlapping boxes stay readable (low-opacity fill, outlined label), and the boxes can be toggled off in the header.

## Notes

Optional polish. Drop it if `ui-feedback` shows it's noise.

## Result
