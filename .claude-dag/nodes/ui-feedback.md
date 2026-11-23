---
id: ui-feedback
title: Try UI on a real project, collect friction
kind: research
status: done
deps: [web-ui, m3-ui-arrange]
milestone: m4-ui-readable
---

## Goal / acceptance

- Use the web UI to plan and track real work on at least one project other than this one, for at least a few sessions, after M3 is released.
- Write a list of friction points in Result, each with a severity: blocker, annoying or nice-to-have.
- Each point is either turned into a node with `/dag:replan` or dismissed with a reason.

## Notes

The plan is to develop the dag with the dag itself. This repo's own plan counts as a test project too, but a second, unrelated project gives a fresh view.
This node comes after M3 so the test covers dragging and safe editing. Its findings may change the M4 tasks.

## Result

I'm using claude-dag to track the development of claude-dag itself, the UI is reasonable now. However, it's not very integrated into claude, it's like having a separate tool for tracking stuff. Let's think about how we can integrate it better. A few options:
- Having chat window on the web UI, add more functionality and button like spawn agent, showing status of how agents are doing the jobs
Remember that the goal is currently trying to keeping track of work that is being done with AI agents

### Friction points (2026-11-22, triaged with Claude)

Tried on this repo only, so far. The UI itself reads fine: no blockers in the graph view.

1. **annoying:** The DAG doesn't know which session works on which node, or how that work is going. The UI shows a plan, not the work happening. → M5 `m5-agent-activity` (hooks link sessions to nodes, activity log, live and stalled markers).
2. **annoying:** The UI is a separate browser tab, away from the editor and the Claude panel. → M6 `m6-vscode` (thin VS Code extension: webview of the same UI, sidebar tree, status bar).
3. **nice-to-have:** You can't start work on a node from the UI. → `vscode-run` (interactive `claude "/dag:next <id>"` in an integrated terminal).
4. **dismissed:** Chat window in the web UI. It would mean rebuilding a Claude Code frontend; the VS Code terminal from `vscode-run` gives you the chat.
5. **dismissed for now:** Headless Run button in the web UI (`claude -p`). It needs permission modes, a security token on the server and `--resume` for follow-ups. Revisit only if work has to be started away from VS Code.

2026-11-22: Closed at the user's request. The trial on a second, unrelated project from the acceptance criteria was waived: only this repo was used.
