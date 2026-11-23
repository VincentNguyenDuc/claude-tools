---
id: yaml-backend
title: Switch the tools, CLI and server to YAML storage
kind: task
status: todo
deps: [yaml-writer]
milestone: m5-yaml-storage
verify: cd plugins/dag && uv run -q --group dev pytest -q
---

## Goal / acceptance

- The MCP tools, CLI, session-start hook and server read and write YAML storage only, and the per-node frontmatter backend is removed.
- `dir_version` / the change token covers the plan YAML files and every referenced body file, not just `nodes/*.md`.
- `dag_show` returns the node's source file and line and its body paths.
- The full suite passes against YAML fixtures.

## Notes

## Result
