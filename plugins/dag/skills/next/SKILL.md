---
name: next
description: Work the next ready node(s) of the project's planning DAG (.claude-dag/). Mark it active, do the work, run its verify check, record the result, and mark it done or failed. Use when asked to continue the plan, do the next task or milestone step, work on a specific node, or "/dag:next [id | count]".
---

Use the `dag_*` MCP tools from the dag plugin. If they aren't available, use the `claude-dag` CLI. Arguments: a node id to work on, or a count of nodes to do one after another (default 1).

1. **Pick.** Call `dag_summary` and `dag_ready`.
   - If an id was given, use it. If it isn't ready, say which deps are still open and ask before going ahead.
   - Otherwise prefer, in order: nodes that are already `active` (unfinished earlier work), then nodes in the earliest unfinished milestone, then nodes that unblock the most others.
   - Say in one line which node you're starting and why.
2. **Claim.** `dag_update(id, status="active")`.
3. **Load context.** Call `dag_show(id)` to read the goal, acceptance criteria and notes. Read the `## Result` of its deps, which is often what this node builds on. Follow the project's own rules (CLAUDE.md and so on).
4. **Do the work**, within the node's scope:
   - `task` / `test`: implement until the acceptance criteria hold.
   - `research`: investigate, then write the findings with `dag_append(id, ..., section="Notes")`.
   - `decision`: write the options, the choice and why. If the decision is really the user's to make, present the options and ask instead of choosing.
   - **Out-of-scope work you discover** becomes new nodes (`dag_add` with the right deps), not scope creep. Mention them to the user.
5. **Verify.**
   - If the node has `verify`, read the command first. Normal build, test and lint commands are fine to run. If it does anything else (network calls, deletion, deploys, unfamiliar scripts), show it and ask first. Then call `dag_verify(id)`, which marks the node done on pass and failed on failure.
   - If there's no `verify`, check each acceptance criterion yourself, then `dag_update(id, status="done")`.
   - **On failure:** fix the problem and verify again, as long as the fix stays within scope. If it's still failing or blocked, leave the node `failed` (or set `blocked`), record why, and suggest `/dag:replan`. Never weaken the verify command or the acceptance criteria to get a pass.
6. **Record.** `dag_append(id, ...)` into `## Result`: what changed (files, commands, commit if any), evidence it works, and any caveats or follow-ups. Keep it short.
7. **Report** in a few lines: what was done, the verify outcome, and what is ready now (`dag_ready`). If a count was given, continue with the next node.

Rules:
- One node at a time by default. Run independent ready nodes in parallel subagents only when the user asks for it. In that case each subagent does steps 3–5 for one node and reports back, and you, the main agent, are the only one who updates the graph.
- Don't commit or push unless the user asks or the project's conventions say to.
- Don't mark a node done without evidence, and don't skip a failing verify.
