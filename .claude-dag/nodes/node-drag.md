---
id: node-drag
title: Drag nodes to move them in the web UI
kind: task
status: done
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
All changes are in `static/index.html`:
- State `positions` / `layoutVer` comes from `GET /api/layout`. `load()` fetches it together with the graph, and an error falls back to `{}`.
- `layout()` has a new step 6: pinned nodes take their saved x/y and edges touching them get `chain = []` (a direct curve). `render()` is split into `render()` (layout) and `draw()` (DOM) so a drag can redraw without running the layout again.
- Plain left-drag on a node: start after more than 3 px of movement, redraw live, and on mouseup round to integers and `PUT /api/layout {positions: {id: pt}}`. Under the threshold it's still a click, so the panel opens. Canvas drag still pans and shift+drag still links. The node mousedown now stops propagation, so dragging a node no longer pans.
- Header **Reset layout** button (with confirm, replace with `{}`, then fit). Panel **Unpin** button, shown only for pinned nodes, which sends `{id: null}`. The tooltip says "(placed by hand)". Help text is updated.
- The poll also watches `layout` from `/api/version` and refetches only the layout when it changes. It skips while a drag or link is in progress.

Tests (`tests/test_ui.py -k drag`, 3 tests): drag pins only the dragged node at the right world position, the long edge goes from 2 curve segments to 1, no panel opens, and after a reload the position is the same and unpinned nodes are unchanged. Then click-with-wobble opens the panel, canvas drag pans, shift+drag adds a dep, and no layout PUT is sent for any of those. Then Unpin returns the node to its automatic place, and Reset asks first (dismiss keeps the positions, accept clears them). Mutation check: removing the pin override or the edge-chain reset makes the tests fail. The full suite is 49 passed.

Caveat: automatically placed nodes can overlap pinned ones, because the automatic layout ignores pins. That's acceptable per the acceptance criteria.
