---
id: activity-log
title: Hooks append per-session activity events
kind: task
status: todo
deps: [activity-design, migrate-this-repo]
milestone: m6-agent-activity
verify: cd plugins/dag && uv run -q --group dev pytest -q tests/test_hooks.py -k activity
---

## Goal / acceptance

- The hooks chosen in `activity-design` are registered in `hooks/hooks.json` and append one event per call in the agreed schema: tool name, a short target (file path, command or dag node id), and a timestamp.
- Turn end (`Stop`), permission or attention prompts (`Notification`), subagent end and `SessionEnd` are recorded too.
- They do nothing outside a project with `.claude-dag/`, never fail the tool call, and stay within the measured time budget.
- Tests feed sample hook JSON on stdin and check the written events.

## Notes

## Result
