---
id: vscode-activity
title: Open touched files and session terminals from activity
kind: task
status: todo
deps: [vscode-webview, vscode-run, ui-activity]
milestone: m7-vscode
verify: cd extensions/dag-vscode && npm test -- --grep activity
---

## Goal / acceptance

- In VS Code, files listed in a node's Activity tab open in the editor when clicked.
- A "waiting for you" node focuses its session's terminal when one is open in this window.

## Notes

## Result
