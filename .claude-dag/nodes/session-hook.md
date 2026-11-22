---
id: session-hook
title: 'SessionStart hook: inject plan summary'
kind: task
status: done
deps: [core-cli]
milestone: m2-claude-loop
verify: CLAUDE_PROJECT_DIR=$PWD bash plugins/dag/hooks/session-start.sh | grep -q 'planning DAG'
---

## Goal / acceptance


## Notes


## Result
hooks/session-start.sh walks up from $CLAUDE_PROJECT_DIR to find .claude-dag/ and prints the summary (max 40 lines). Silent when there is no plan. Confirmed in a headless E2E run.
