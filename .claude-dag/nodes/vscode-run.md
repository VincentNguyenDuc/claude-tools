---
id: vscode-run
title: Run a node in a Claude terminal
kind: task
status: todo
deps: [vscode-tree, vscode-webview]
milestone: m7-vscode
verify: cd extensions/dag-vscode && npm test -- --grep run
---

## Goal / acceptance

- A "Run with Claude" action on ready nodes, in the tree context menu and in the graph panel, opens an integrated terminal named after the node and runs `claude "/dag:next <id>"` in the workspace.
- If a terminal for that node is already open, it's focused instead of starting a second session.

## Notes

Running nodes in parallel in one checkout will make sessions overwrite each other. Warn when another node is already active, and leave worktree support for later.

## Result
