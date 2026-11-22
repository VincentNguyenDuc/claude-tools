---
id: body-preview
title: Rendered markdown preview of node bodies
kind: task
status: todo
deps: [ui-test-harness]
milestone: m4-ui-readable
verify: cd plugins/dag && uv run -q --group dev pytest -q tests/test_ui.py -k preview
---

## Goal / acceptance

- The panel shows the body rendered (headings, lists, checkboxes, inline and fenced code, links), with an Edit toggle back to the textarea.
- All HTML in node bodies is escaped. A test shows that `<script>` and `onerror=` in a body don't execute.
- Links open in a new tab with `rel=noopener`, and only http(s) links are allowed.

## Notes

No CDN and no npm: use a small inline renderer for the markdown subset the plan bodies actually use. The page is served from localhost and can edit files, so XSS here matters.

## Result
