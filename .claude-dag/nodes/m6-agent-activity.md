---
id: m6-agent-activity
title: 'M6: see what agents are doing'
kind: milestone
status: todo
deps: [m5-yaml-storage]
---

## Goal / acceptance

- For every `active` node you can see which Claude session is on it and its state: running, waiting for you, idle, or ended. You can also see what it has done recently.
- An active node whose session has ended is flagged as stalled in the UI, in `dag_summary` and in the session-start summary.
- Released as dag 0.6.0.

## Notes

Comes from `ui-feedback`: the DAG only knows what Claude writes into it, so the UI shows a plan, not the work happening. Hook-based tracking is needed whatever front end shows it (web UI or the M7 VS Code extension).
Built on the M5 YAML storage. Was M5 until the storage milestone was inserted before it (2026-11-22).

## Result
