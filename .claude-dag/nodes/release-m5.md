---
id: release-m5
title: Release dag 0.5.0
kind: task
status: todo
deps: [yaml-docs]
milestone: m5-yaml-storage
verify: claude plugin validate . && claude plugin validate plugins/dag
---

## Goal / acceptance

- The version is raised to 0.5.0 in the same places as `release-m4`, and `uv lock` is refreshed.
- The full test suite passes and the installed plugin is updated. The release notes call out the storage change and `claude-dag migrate`.

## Notes

## Result
