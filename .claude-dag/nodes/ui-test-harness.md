---
id: ui-test-harness
title: Decide and set up how to test the web UI
kind: decision
status: todo
deps: []
milestone: m3-ui-arrange
verify: cd plugins/dag && uv run -q --group dev pytest -q tests/test_ui.py
---

## Goal / acceptance

- A choice is recorded in Result with the reason.
- `tests/test_ui.py` exists and contains at least one smoke test: start the server against a temp `.claude-dag/`, load the page, and check that the nodes render with no JS console errors.
- Tests skip cleanly (they don't fail) when the browser or runtime isn't installed.
- How to install the test browser is documented in the README's dev section.

## Notes

Options:
- **Playwright for Python** (recommended): a dev dependency that drives a real Chromium, so it can test dragging, hover and keyboard. Costs a one-time ~150 MB `playwright install chromium`.
- **`node --check` on the extracted `<script>`**: syntax only, can't test behaviour. The local `node` is currently broken (Homebrew `simdutf` dylib missing).
- **Manual only**: no automated check, so the UI nodes would have no meaningful verify.

The UI is a single static `index.html` with no build step. Keep it that way: no npm toolchain.

## Result
