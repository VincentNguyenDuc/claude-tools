---
id: yaml-writer
title: Round-trip writes to YAML and body files
kind: task
status: todo
deps: [yaml-loader]
milestone: m5-yaml-storage
verify: cd plugins/dag && uv run -q --group dev pytest -q tests/test_yaml.py -k write
---

## Goal / acceptance

- Every graph change works in place in whichever file defines the node, and keeps comments, key order and indentation: add, update, rename (which updates references in every file), remove, link, unlink and status changes.
- Body writes (`dag_append`, body updates) go to the node's markdown file as the spec says.
- Each write re-reads the file just before writing and writes atomically. If the file no longer parses, the write is refused with a clear error instead of overwriting a half-finished hand edit.
- Tests: hand-formatted fixtures with comments come back byte-identical except for the intended change.

## Notes

This replaces the M3 conflict checks for UI edits; the UI no longer writes. The remaining risk is a tool write landing while the user is editing the same file. Re-reading first plus the editor's own reload-on-change covers that.

## Result
