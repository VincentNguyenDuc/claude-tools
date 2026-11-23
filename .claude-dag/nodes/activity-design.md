---
id: activity-design
title: 'Design session tracking: hook events, storage, cost'
kind: research
status: todo
deps: []
milestone: m6-agent-activity
---

## Goal / acceptance

- Confirm from the Claude Code hooks docs what each event gives us: `PostToolUse`, `Stop`, `SubagentStop`, `Notification`, `SessionStart` and `SessionEnd`. Fields of interest: `session_id`, `transcript_path`, `cwd`, `tool_name`, `tool_input`.
- Decide and write down in Result:
  - the storage layout (e.g. `.claude-dag/activity/<session>.jsonl`), and whether it is gitignored (likely yes: machine-local and noisy);
  - the event schema;
  - how a session is linked to a node;
  - how the state is derived (running / waiting for you / idle / ended / stalled) and the idle timeout;
  - the size cap or rotation.
- Pick a hook runtime that adds under ~50 ms per tool call, measured. The hook runs on every tool call in every session, so `uv run` startup may be too slow; a stdlib `python3 -I` script or plain bash are options.

## Notes

The hook must be silent and exit 0 when there's no `.claude-dag/` or on any error, like `hooks/session-start.sh`.

## Result
