---
id: milestone-groups
title: Draw a box around each milestone's members
kind: task
status: done
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
- `static/index.html`: a new `#groups` layer sits behind the edges. `drawGroups()` boxes each milestone's visible members (nodes whose `milestone` is it) on every `draw()`, so the box follows pins and drags live. Each milestone gets its own hue (golden-angle spacing). The fill is about 7% opacity, with a dashed outline and a label outlined in the background colour. Boxes use `pointer-events: none`, so panning and clicks pass through, and they dim in trace mode.
- A "groups" checkbox in the header turns them off; the choice is kept in `localStorage` (`dag.groups`).
- Test `test_groups_box_members_follow_drag_and_toggle`: covers membership, containment, following a drag, hiding when no members are visible (with hide done), and the toggle surviving a reload. Full suite 57 passed. Checked on this repo's 52-node plan in light and dark.
- Caveat: auto-layout doesn't take groups into account, so boxes overlap when a milestone's members are spread across columns. The fill stays readable.
