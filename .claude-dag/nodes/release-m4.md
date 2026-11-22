---
id: release-m4
title: Release dag 0.4.0
kind: task
status: todo
deps: [node-labels, hover-trace, node-search, body-preview, milestone-groups, ui-feedback]
milestone: m4-ui-readable
verify: claude plugin validate . && claude plugin validate plugins/dag
---

## Goal / acceptance

- The version is raised to 0.4.0 in the same four places as `release-m3`, and `uv lock` is refreshed.
- The README is updated, the full test suite passes, and the installed plugin is updated.

## Notes

## Result
