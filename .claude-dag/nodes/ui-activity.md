---
id: ui-activity
title: Live and stalled markers and an activity tab in the web UI
kind: task
status: todo
deps: [activity-api]
milestone: m6-agent-activity
verify: cd plugins/dag && uv run -q --group dev pytest -q tests/test_ui.py -k activity
---

## Goal / acceptance

- Active nodes show a live marker: running (animated), waiting for you, idle or stalled, plus how long they have been running.
- The node panel gets an Activity tab with the recent events of each linked session and the files touched.
- Updates come through the existing refresh mechanism, with no manual reload.

## Notes

## Result
