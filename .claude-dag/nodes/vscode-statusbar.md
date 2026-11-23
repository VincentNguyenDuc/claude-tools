---
id: vscode-statusbar
title: 'Status bar item: active node and milestone progress'
kind: task
status: todo
deps: [vscode-tree]
milestone: m7-vscode
verify: cd extensions/dag-vscode && npm test -- --grep statusbar
---

## Goal / acceptance

- Shows something like `◆ M4 5/8 · node-labels`: the active milestone's progress and the active node, or the ready count when nothing is active. It flags stalled nodes once M5's activity data is there.
- Clicking it opens the graph panel.

## Notes

## Result
