---
id: vscode-tree
title: Sidebar tree of milestones and nodes
kind: task
status: todo
deps: [vscode-server]
milestone: m7-vscode
verify: cd extensions/dag-vscode && npm test -- --grep tree
---

## Goal / acceptance

- An activity-bar view lists milestones with their members, plus a section for nodes without a milestone. Each item has a status icon and shows its title.
- Clicking a node opens its `.md` file. The tree refreshes when anything under `.claude-dag/` changes.

## Notes
After M5, clicking a node opens its definition in the plan YAML (file and line), with its body file one action away. Refresh when anything under `.claude-dag/plan/` or a referenced body file changes.

## Result
