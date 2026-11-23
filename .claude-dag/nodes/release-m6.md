---
id: release-m6
title: Release dag 0.6.0
kind: task
status: todo
deps: [ui-activity]
milestone: m6-agent-activity
verify: claude plugin validate . && claude plugin validate plugins/dag
---

## Goal / acceptance

- The version is raised to 0.6.0 in the same places as `release-m5`, and `uv lock` is refreshed.
- The README documents activity tracking and what the hooks record. The full test suite passes and the installed plugin is updated.

## Notes

## Result
