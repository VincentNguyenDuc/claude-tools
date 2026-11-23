---
id: vscode-webview
title: 'Graph panel: the web UI in a webview'
kind: task
status: todo
deps: [vscode-server]
milestone: m7-vscode
verify: cd extensions/dag-vscode && npm test -- --grep webview
---

## Goal / acceptance

- A command ("DAG: Open graph") opens the existing UI in a webview panel. Viewing, dragging and editing work as in the browser, including over Remote SSH.
- The UI can tell when it runs inside VS Code, so host-only actions (Run, open file) can show up there.

## Notes

Choose one: an iframe to localhost through webview `portMapping` / `asExternalUri`, with the UI messaging the parent window; or load `index.html` into the webview directly, with a configurable API base and `acquireVsCodeApi`. Write down the choice and why.

After M5 the UI is read-only, so the panel only views the plan. Host actions are Run, and opening the node's YAML line or body file in the editor (instead of `vscode://` links).

## Result
