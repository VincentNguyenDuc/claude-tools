---
id: activity-api
title: Expose node activity in the API, CLI and summary
kind: task
status: todo
deps: [session-binding]
milestone: m6-agent-activity
verify: cd plugins/dag && uv run -q --group dev pytest -q tests/test_server.py tests/test_cli.py tests/test_mcp.py -k activity
---

## Goal / acceptance

- A server endpoint returns, for each node, its linked sessions with the derived state and their recent events.
- `claude-dag activity [id]` prints the same information.
- `dag_summary`, `claude-dag summary` and so the session-start hook list stalled nodes: active, but the session has ended or gone idle past the timeout.

## Notes

## Result
