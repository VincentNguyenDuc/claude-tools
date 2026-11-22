---
name: validate
description: Check the project's planning DAG (.claude-dag/) for problems such as missing references, bad fields or cycles, and suggest fixes. Use when asked to validate, lint or sanity-check the plan, or "/dag:validate".
---

Use the `dag_*` MCP tools from the dag plugin. If they aren't available, use `claude-dag validate`.

1. Call `dag_validate`.
2. If it returns an empty list, say the graph is valid in one line and stop.
3. Otherwise list each problem with the node it affects and a concrete fix (call `dag_show` on a node if you need its details to suggest one).
4. Offer to apply the fixes with `dag_update`, `dag_link` or `dag_unlink`, or to run `/dag:replan` if the problems mean the plan itself needs rethinking. Don't change anything until the user agrees.
