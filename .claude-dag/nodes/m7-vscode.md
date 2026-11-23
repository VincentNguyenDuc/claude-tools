---
id: m7-vscode
title: 'M7: the DAG inside VS Code'
kind: milestone
status: todo
deps: [m6-agent-activity]
---

## Goal / acceptance

- A VS Code extension shows the graph next to the Claude Code panel, with a sidebar tree and a status bar item. From a node you can start a Claude session that works on it.
- It is a thin shell. Graph logic, the file format and the API stay in the Python package, and the graph panel reuses the web UI's `index.html`.
- It installs from a `.vsix` file.

## Notes

Comes from `ui-feedback`. Running a node in an integrated terminal (interactive `claude`) replaces a headless Run button in the web UI: permissions work as usual, follow-ups are typed in the terminal, and the server doesn't need to spawn processes. That button is out of scope unless it's needed away from VS Code.

## Result
