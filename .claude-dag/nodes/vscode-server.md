---
id: vscode-server
title: Extension starts or reuses the claude-dag server
kind: task
status: todo
deps: [vscode-scaffold]
milestone: m7-vscode
verify: cd extensions/dag-vscode && npm test -- --grep server
---

## Goal / acceptance

- The extension finds `claude-dag`, reuses a server already running for this project or starts one on a free port, and stops the one it started when it deactivates.
- Decide and note how `claude-dag` is found: a setting, `PATH`, or the installed plugin under `~/.claude/plugins/cache/...` (the path includes the version).
- Any server changes this needs, such as `--port 0` with the chosen port printed, or a health endpoint, are made in the Python package with tests.

## Notes

## Result
