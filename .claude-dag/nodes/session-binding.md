---
id: session-binding
title: Link sessions to the nodes they work on
kind: task
status: todo
deps: [activity-log]
milestone: m6-agent-activity
verify: cd plugins/dag && uv run -q --group dev pytest -q tests/test_hooks.py -k binding
---

## Goal / acceptance

- When a session sets a node `active` (through `dag_update`, the CLI or `/dag:next`), the session is recorded as working on that node. The link ends when the node becomes done, failed, blocked or dropped, or when another session takes it over.
- It works without Claude doing anything extra: the link comes from hook input, not from tool arguments.
- Tests cover activation, completion, takeover by a second session, and two sessions on two nodes.

## Notes

## Result
