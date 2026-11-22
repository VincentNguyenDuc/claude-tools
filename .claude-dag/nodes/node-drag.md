---
id: node-drag
title: Drag nodes to move them in the web UI
kind: task
status: todo
deps: [layout-store, ui-test-harness]
milestone: m3-ui-arrange
verify: cd plugins/dag && uv run -q --group dev pytest -q tests/test_ui.py -k drag
---

## Goal / acceptance

- Plain drag on a node moves it; the position is saved to `/api/layout` on mouseup and survives a reload.
- Click without moving (under a ~3 px threshold) still opens the edit panel. Dragging the canvas still pans, and shift+drag between nodes still creates a dependency.
- Nodes that have been moved are pinned and keep their saved position. All other nodes are still placed automatically.
- Edges touching a pinned node are drawn as a direct curve instead of being routed through the layout's waypoints.
- A "Reset layout" button in the header clears all positions (after confirmation). Each node also has an "Unpin" action in the panel.
- `pytest -k drag` covers: drag, reload, same position; click still opens the panel; reset.

## Notes

Current layout code is in `static/index.html` (`layout()`, `edgePath()`). Simplest approach: run the automatic layout, then override the positions of pinned nodes.

## Result
