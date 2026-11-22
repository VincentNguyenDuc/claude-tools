---
id: node-search
title: Search nodes by title or id
kind: task
status: done
deps: [ui-test-harness]
milestone: m4-ui-readable
verify: cd plugins/dag && uv run -q --group dev pytest -q tests/test_ui.py -k search
---

## Goal / acceptance

- `/` (or ⌘K) opens a search box that matches titles and ids as you type, case-insensitively.
- Enter centres the view on the match and selects it. Esc closes the box.
- A match hidden by the current filter clears that filter so the node can be shown.

## Notes

## Result
All changes are in `static/index.html`:
- A `#search` box floats over the canvas. `/` opens it (unless you're in a text field) and so does ⌘K/Ctrl+K (anywhere). Matching is a case-insensitive substring on id and title, ranked exact → prefix → contains, with up to 50 results showing title, id and status. ↑/↓ move, Enter or click picks, and Esc or blur closes. The input's keydown stops propagation, so Esc doesn't also close the panel and N/F/Delete don't fire.
- `goToNode(id)`: if the node is hidden, it clears only the filter that hides it (the milestone filter if the node isn't that milestone or one of its members, hide-done if the node is done or dropped). Then it opens the node in the panel (which selects it) and `centerOn(id)` centres it in the stage after the panel has resized it. Help text is updated.
- **Bug fixed along the way:** the shortcut handler treated any focused `<input>` (including the hide-done checkbox) as typing, so shortcuts stopped working after you clicked a filter. Now only text fields block all shortcuts, a focused select blocks letters but not `/`, and checkboxes and radios block nothing.
- Tests (`-k search`, 2 tests): case-insensitive id/title matches, ranking, no match, Enter selects and centres (within 3 px), ⌘/Ctrl+K, ArrowDown, and Esc closing only the box. Hide-done is cleared for a done match. The milestone filter is kept for a member and cleared for a non-member. The full suite is 55 passed.
