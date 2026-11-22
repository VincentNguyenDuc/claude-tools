---
id: node-labels
title: Wrap node titles instead of truncating
kind: task
status: done
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
All changes are in `static/index.html`:
- Text is measured with a canvas `measureText` using the page font (`textW`). `wrapTitle` does a greedy word wrap to at most 2 lines, hard-breaks overlong words, and puts an ellipsis only at the end of line 2 (`fitText`).
- **Widths per column:** each layout column is as wide as its widest id/status line needs (`NW=210` up to `NW_MAX=480`), so one long id widens only its own column. Titles wrap at that width. Height = `NH` + `LINE_H` (16) per extra title line, so 52 or 68. Layout items carry `w/h/lines`, and column x is cumulative.
- Every use of the fixed `NW/NH` (edge anchors, waypoints, drag line, `centerOn`, rect, text y) now uses per-item `w/h`. The status line sits at `h-13`. The full title is still in the `<title>` tooltip.
- `NW_MAX` is 480 rather than 400, because a 30-char id of `m`s plus "milestone" and counts needs about 450 px.
- Test (`-k labels`): a short title gives 1 line and 52 px. A two-line title wraps with no ellipsis. A long title gives 2 lines with … only at the end. Every line fits within `w-20` (`getComputedTextLength`). A 30-char id on a blocked decision and on a milestone with counts is not cut. Only the long-id columns widen. No two node boxes overlap. The full suite is 56 passed.
- Checked visually on this repo's own plan with a 1600×900 screenshot: wrapping, trace highlighting and the notes preview all render cleanly.
