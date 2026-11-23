---
id: vscode-scaffold
title: Scaffold the VS Code extension package
kind: task
status: todo
deps: [migrate-this-repo]
milestone: m7-vscode
verify: cd extensions/dag-vscode && npm ci && npm test
---

## Goal / acceptance

- A TypeScript extension package in `extensions/dag-vscode/` with build, lint and a test runner where `npm test -- --grep <name>` runs a subset.
- It activates on `workspaceContains:.claude-dag`.
- `node_modules` and build output are gitignored, and the repo README mentions the package.

## Notes

## Result
