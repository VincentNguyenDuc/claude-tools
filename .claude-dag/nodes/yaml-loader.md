---
id: yaml-loader
title: Load the graph from YAML plan files
kind: task
status: todo
deps: [yaml-format, release-m4]
milestone: m5-yaml-storage
verify: cd plugins/dag && uv run -q --group dev pytest -q tests/test_yaml.py -k load
---

## Goal / acceptance

- All plan files are parsed with `ruamel.yaml` into the existing graph model, following the spec, and every node keeps its source location (file and line).
- Bodies are read from the markdown files their `body:` points to.
- Errors are reported with `file:line`: duplicate ids across files, unknown `after:` or `body:` targets, reserved-key clashes, invalid YAML and cycles that cross files.

## Notes

## Result
