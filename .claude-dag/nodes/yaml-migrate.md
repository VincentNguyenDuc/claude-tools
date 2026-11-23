---
id: yaml-migrate
title: 'claude-dag migrate: frontmatter nodes to YAML'
kind: task
status: todo
deps: [yaml-writer]
milestone: m5-yaml-storage
verify: cd plugins/dag && uv run -q --group dev pytest -q tests/test_yaml.py -k migrate
---

## Goal / acceptance

- `claude-dag migrate [--dry-run]` converts `nodes/*.md` into `plan/*.yaml`, one file per milestone plus one for nodes without a milestone. It nests nodes where the deps form a tree, uses `after:` for the rest, and moves each body into a markdown file that `body:` points to.
- It refuses to run if `plan/` already exists, and leaves the old files in a backup until the user deletes them.
- Test: on fixture plans, the migrated graph is identical to the original (ids, fields, deps, statuses, bodies).

## Notes

## Result
