---
id: ui-test-harness
title: Decide and set up how to test the web UI
kind: decision
status: done
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
**Decision: Playwright for Python.** It's the only option that can test behaviour (drag, hover, keys), which the downstream M3/M4 UI nodes need. It needs no npm toolchain, and `node` is broken locally anyway. Manual-only would leave those nodes with no real verify.

- `pyproject.toml` / `uv.lock`: dev group gains `playwright>=1.65.2`.
- `tests/test_ui.py`: a module-scoped `browser` fixture (skips if Playwright isn't importable or Chromium can't launch), a `dag` fixture (temp `.claude-dag/` + `make_server(port=0)`), and a `page` fixture that collects `pageerror` and console errors into `page.js_errors`. Smoke test: 3 nodes (milestone + 2 tasks with a dep) render as `#nodes .node[data-id]`, the edge exists, and there are no JS errors.
- README Develop section: `uv run --group dev playwright install --only-shell chromium`.

Evidence: it skipped cleanly before the browser was installed ("Executable doesn't exist…"). After install, verify passes (1 passed, 0.8 s). The full suite is 36 passed.

Notes for UI nodes: SVG `<g>` has no innerText, so use `text_content()`. Reuse the `dag`/`page` fixtures. The installed Chromium build is 1255, so if Playwright gets bumped, the browser needs a reinstall.
