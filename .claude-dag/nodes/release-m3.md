---
id: release-m3
title: Release dag 0.3.0
kind: task
status: todo
deps: [node-drag, safe-edits]
milestone: m3-ui-arrange
verify: claude plugin validate . && claude plugin validate plugins/dag
---

## Goal / acceptance

- The version is 0.3.0 in `plugins/dag/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `plugins/dag/pyproject.toml` and `src/claude_dag/__init__.py`, and `uv lock` is refreshed.
- The README documents dragging, Reset layout and conflict handling.
- The full test suite passes, the installed plugin is updated through `/plugin`, and the new cache directory `~/.claude/plugins/cache/claude-tools/dag/0.3.0/` exists.

## Notes

Installed plugins run from a cache keyed by version, so repo edits don't take effect until the version is raised and the plugin is updated. This bit us at 0.2.1 (`/dag:validate` and `/dag:ui`).

## Result
