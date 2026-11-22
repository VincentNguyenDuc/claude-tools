---
name: plan
description: Turn a goal into a planning DAG in .claude-dag/ with milestones, tasks with dependencies, acceptance criteria and verify checks. Use when asked to plan a project, feature or long effort as a DAG, break work into milestones, extend an existing plan, or "/dag:plan <goal>".
---

The plan is a graph of nodes stored in the project's `.claude-dag/`. Work with it through the `dag_*` MCP tools from the dag plugin. If those tools aren't available, use the `claude-dag` CLI, which has the same operations (see `claude-dag --help`).

1. **Load what exists.** Call `dag_summary`.
   - If there is no `.claude-dag/`, say you'll create one and call `dag_init`.
   - If a plan exists, call `dag_list` and extend it. Don't duplicate nodes that already exist, and attach new work to existing milestones where it fits.
2. **Understand the goal.** Read the relevant code, docs and CLAUDE.md first. Ask only the questions whose answers change the shape of the plan. For everything else, choose a sensible default and note it in the node.
3. **Draft the graph:**
   - **Milestones** (`kind: milestone`): usually 2–5, each a state you could demo or ship. Chain them with `deps` (M2 depends on M1). Give tasks `milestone: <id>`.
   - **Tasks** sized for one focused session, about one PR. Split anything bigger.
   - **Dependencies only where they're real**, so independent work shows up as ready in parallel.
   - **Unknowns become nodes:** a `research` node to find out, or a `decision` node to choose. Place them *before* the tasks that depend on them instead of guessing.
   - **`verify`** whenever an automated check exists: the exact command, run from the project root (for example `uv run pytest tests/test_x.py`, `npm test -- foo`, `make lint`). Use `test` nodes for dedicated test work.
   - **Body:** under `## Goal / acceptance`, write concrete, checkable outcomes. Put context, constraints and options under `## Notes`. Leave `## Result` empty.
   - **ids:** short kebab-case (`auth-api`, `m1-mvp`).
4. **Show the draft before writing it.** Give a compact outline grouped by milestone, one line per node: `id: title (deps) [verify]`. Call out assumptions and the research/decision nodes. Ask for a go-ahead.
5. **Write it in one call** with `dag_add_many`. Nodes may reference each other in any order, and the write is all or nothing. Then run `dag_validate` and fix any problems.
6. **Finish** with `dag_summary`, naming what is ready to start. Offer `/dag:next` to begin, and `dag_open_ui` to see the graph.

Rules:
- Planning never marks work as done and never changes code.
- Keep reasoning in the nodes, not only in chat: why a node exists, and the alternatives considered.
- Record notable planning decisions with `dag_log`.
