---
id: migrate-this-repo
title: Migrate this repo's own plan to YAML
kind: task
status: todo
deps: [release-m5]
milestone: m5-yaml-storage
verify: cd plugins/dag && uv run -q claude-dag -C ../.. validate
---

## Goal / acceptance

- After installing 0.5.0 and restarting the session, `claude-dag migrate` is run on this repo's `.claude-dag/`. Node counts, statuses and bodies match the old plan, and the backup is removed once the user agrees.

## Notes

This has to wait until 0.5.0 is installed. The running MCP server and session hook come from the installed plugin, and before 0.5.0 they can't read YAML, so migrating earlier would cut this session off from its own plan.

## Result
