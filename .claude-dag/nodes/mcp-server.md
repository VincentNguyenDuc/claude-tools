---
id: mcp-server
title: MCP server exposing graph tools
kind: task
status: done
deps: []
milestone: m2-claude-loop
verify: cd plugins/dag && uv run -q --group dev pytest -q tests/test_mcp.py
---

## Goal / acceptance


## Notes


## Result
plugins/dag/src/claude_dag/mcp_server.py: 16 dag_* tools on MCP SDK 2.x (MCPServer). DagError is re-raised as ToolError so Claude sees the message. Tested in-process, over stdio, and end to end through `claude -p --plugin-dir` (connects in ~270ms).
