---
name: ui
description: Open the web UI for the project's planning DAG (.claude-dag/) in the browser. Use when asked to see, show, view or open the graph or plan visually, or "/dag:ui".
---

Use the `dag_*` MCP tools from the dag plugin.

1. Call `dag_open_ui(open_browser=true)`.
2. Give the user the URL in one line.
3. Mention that the UI runs only while this session is running. For a standalone server, use `claude-dag serve --open`.
