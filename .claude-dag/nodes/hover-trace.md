---
id: hover-trace
title: Highlight a node's upstream and downstream chain
kind: task
status: done
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
All changes are in `static/index.html`:
- `applyTrace()`: the focus is the hovered node, otherwise the selected one (not while creating). `traceSets()` runs a DFS backward (up) and forward (down) over `edgesOf(graph.nodes)`. That's the **whole graph**, so chains through filtered-out nodes still connect. It also includes member→milestone edges, so a milestone lights up from its members.
- Lit nodes are those in up ∪ down. An edge is lit when both ends are in `up` or both are in `down`, so sibling branches stay dim. `#canvas.trace` dims everything that isn't lit (nodes to 0.25, edges to 0.12), and lit edges are drawn bolder. Edge paths now carry `data-from`/`data-to`.
- Only classes are toggled, so there's no re-layout. The trace is applied on node mouseenter/mouseleave and at the end of every `draw()`, so it survives polls and drags.
- Tests (`-k trace`, 2 tests): hovering shows the exact node and edge sets (the sibling branch stays dim), mouse-out clears the highlight, selection stays lit after mouse-out, hover beats selection, and closing the panel clears it. Filters: with hide-done, c→(hidden b)→a still lights a; the milestone filter case also works. Mutation check: computing over visible edges only fails the filter test. The full suite is 53 passed.
- The test `page` fixture now uses a 1600×900 viewport, so the open panel doesn't cover nodes.
