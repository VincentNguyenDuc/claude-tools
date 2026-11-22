---
id: skill-next
title: 'Skill: /dag:next (do ready nodes, verify, update)'
kind: task
status: done
deps: [mcp-server]
milestone: m2-claude-loop
verify: claude plugin validate plugins/dag
---

## Goal / acceptance


## Notes


## Result
skills/next/SKILL.md: claim, load context, do the work, verify, record, report. Parallel subagents only when the user asks; only the main agent edits the graph.
