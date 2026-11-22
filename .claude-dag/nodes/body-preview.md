---
id: body-preview
title: Rendered markdown preview of node bodies
kind: task
status: done
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
All changes are in `static/index.html`:
- `mdRender` / `mdInline` / `mdLink` form a renderer for the markdown subset plan bodies use: headings, paragraphs, ul/ol with nesting by indent, `- [ ]`/`- [x]` task items (disabled checkboxes), list continuation lines, fenced ``` / ~~~ code, inline code, **bold**, *italic*, blockquotes, `---` rules, `[text](url)` and bare http(s) URLs. It only uses `createElement` and text nodes, never `innerHTML`. Links must match `^https?://` and get `target=_blank rel="noopener noreferrer"`. Anything else (javascript:, data:) stays literal text.
- Panel: the Notes area shows the rendered preview for existing nodes. **Edit**/**Preview** toggle (`#body-toggle`), and double-clicking the preview opens the editor. New nodes start in edit mode. The mode persists across refills of the same node. Save still reads the textarea, so it works from either mode.
- Tests (`-k preview`, 2 tests): rendering of every supported element plus link attributes and the Edit→Preview round trip. Escaping: `<script>`, `<img onerror>`, an HTML tag in a heading, `javascript:`/`data:` links and `<svg onload>` in inline code. No elements are created, `window.__pwned` stays unset after click and hover, and the text is shown literally. Mutation check: replacing the renderer with `innerHTML` fails the test (5 elements injected). Existing panel tests now use an `edit_body()` helper. The full suite is 51 passed.
