---
id: hover-trace
title: Highlight a node's upstream and downstream chain
kind: task
status: todo
deps: [ui-test-harness]
milestone: m4-ui-readable
verify: cd plugins/dag && uv run -q --group dev pytest -q tests/test_ui.py -k trace
---

## Goal / acceptance

- Hovering or selecting a node highlights all its transitive dependencies and dependents, together with the edges between them, and dims everything else.
- Moving the mouse off the node clears the highlight, unless the node is selected.
- Works with filtered views (milestone filter, hide done).

## Notes

## Result
