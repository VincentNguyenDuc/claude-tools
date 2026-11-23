---
id: vscode-package
title: Package the extension as a .vsix
kind: task
status: todo
deps: [vscode-run, vscode-statusbar, vscode-activity]
milestone: m7-vscode
verify: cd extensions/dag-vscode && npm test && npx -y @vscode/vsce package --out dist/
---

## Goal / acceptance

- `vsce package` builds a `.vsix` with no warnings.
- The README covers install (`code --install-extension`), settings, and how it relates to the dag plugin, which it requires.
- It is installed locally and checked by hand on this repo. Marketplace publishing is a separate decision.

## Notes

## Result
