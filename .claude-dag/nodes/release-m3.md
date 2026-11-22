---
id: release-m3
title: Release dag 0.3.0
kind: task
status: active
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

Progress so far (2026-11-21): the version is 0.3.0 in plugin.json, marketplace.json, pyproject.toml and `__init__.py`, and `uv lock` is refreshed. The README documents drag/pin/Unpin/Reset layout and Save conflict handling. The full suite is 49 passed, and both `claude plugin validate` checks pass.
Still open: the marketplace is installed from GitHub (VincentNguyenDuc/claude-tools), so the 0.3.0 cache needs commit + push and then `claude plugin update dag@claude-tools`. Note that the installed cache was still 0.2.0, which means 0.2.1 was never installed either.

## Result
