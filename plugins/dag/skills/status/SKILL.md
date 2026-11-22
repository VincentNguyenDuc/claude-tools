---
name: status
description: Show where the project's planning DAG (.claude-dag/) stands. Covers milestone progress, what's active, ready, failed or blocked, and what to do next, and can open the web UI. Use when asked about plan status or progress, "where are we", "what's next", or "/dag:status".
---

Use the `dag_*` MCP tools from the dag plugin. If they aren't available, use the `claude-dag` CLI.

1. Call `dag_summary`. If something is failed or blocked, also call `dag_show` on those nodes to give the reason in one line each.
2. Report briefly:
   - progress per milestone
   - what's in progress
   - what's ready, with the 1–3 best next picks and why
   - anything failed or blocked, and what would unblock it
   - any problems reported by `dag_validate`
3. Offer the next step: `/dag:next` to continue, or `/dag:replan` if something is stuck.
4. If the user wants to see the graph, call `dag_open_ui(open_browser=true)` and give them the URL. The UI runs only while this session is running. For a standalone server, use `claude-dag serve --open`.
