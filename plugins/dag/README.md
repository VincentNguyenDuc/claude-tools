# claude-dag

A planning DAG for long-running work. The plan lives as markdown files in the
project's `.claude-dag/`, versioned with the code. You and Claude both read and
edit it, through the CLI, the web UI, or by editing the files directly.

## Install

```sh
claude plugin install dag@claude-tools          # skills + MCP tools + SessionStart hook (needs `uv`)
uv tool install --editable ~/dev/PERSONAL/claude-tools/plugins/dag   # optional: `claude-dag` CLI on PATH
```

The plugin runs its Python code with `uv run --project <plugin dir>`. The first
start creates a virtualenv inside the plugin directory, which takes a few seconds.

## In Claude Code

| | |
|---|---|
| `/dag:plan <goal>` | Break a goal into milestones and tasks with deps, acceptance criteria and verify commands. Shows a draft first, then writes it in one call. |
| `/dag:next [id \| n]` | Pick a ready node: mark it active, do the work, run verify, record the Result, mark it done or failed. |
| `/dag:replan [why]` | After a failure or a change of scope: add, split, re-link or drop nodes and log the reason. |
| `/dag:status` | Progress, what's next, what's stuck. Can open the web UI. |
| `/dag:validate` | Check the graph for missing references, bad fields and cycles, and suggest fixes. |
| `/dag:ui` | Open the web UI in the browser (runs while the session is running). |
| MCP tools | `dag_summary`, `dag_list`, `dag_show`, `dag_ready`, `dag_add`, `dag_add_many`, `dag_update`, `dag_append`, `dag_link`, `dag_unlink`, `dag_remove`, `dag_verify`, `dag_log`, `dag_validate`, `dag_init`, `dag_open_ui` |
| SessionStart hook | In projects that have a `.claude-dag/`, adds a short plan summary to the session context. Does nothing in other projects. |

The MCP server finds the plan by searching upward from `$CLAUDE_PROJECT_DIR`.

## Files

```
.claude-dag/
  nodes/<id>.md     # one node per file
  log.md            # append-only: adds, status changes, verify results, notes
```

```markdown
---
id: cli-core
title: Core library + CLI
kind: task            # task | milestone | research | decision | test
status: todo          # todo | active | blocked | done | failed | dropped
deps: [schema]        # ids this node depends on
milestone: m1         # optional: the milestone this node belongs to
verify: uv run pytest # optional: must pass for `claude-dag verify` to mark it done
---

## Goal / acceptance
## Notes
## Result
```

Unknown frontmatter keys are kept as they are. The file name is the id.

### Derived status

- **ready**: a `todo` node whose deps are all `done` or `dropped`. It is never stored in the file.
- **milestone**: derived from its deps plus its members (nodes with `milestone: <id>`).
  It's `done` when all of them are satisfied, `failed` if any failed, and `active` once work has started.
- Changes that would create a cycle are rejected. Problems in hand-edited files are reported by `validate`.

## CLI

```sh
claude-dag init                                   # .claude-dag/ at the git root
claude-dag add "Ship v1" --id v1 -k milestone
claude-dag add "Schema" -m v1
claude-dag add "Core lib" -d schema -m v1 -v "uv run pytest"
claude-dag link schema core-lib                   # core-lib depends on schema
claude-dag ready                                  # what can be worked on now
claude-dag start schema && claude-dag done schema
claude-dag verify core-lib                        # runs verify -> done / failed
claude-dag list [-s ready] [-m v1] [--json]
claude-dag summary
claude-dag edit core-lib --add-dep x --rename core
claude-dag validate
claude-dag log "decided to use X because Y"
claude-dag append core-lib "shipped in abc123"   # add to ## Result (--section Notes)
claude-dag import plan.yaml                       # many nodes at once, all or nothing
claude-dag serve --open                           # web UI on http://127.0.0.1:8765
```

## Web UI

`claude-dag serve` starts a localhost-only server for the nearest `.claude-dag/`.

- Nodes are laid out left to right by dependency and colored by status.
- Click a node to edit it. Double-click the canvas or press **N** to add one.
- **Shift+drag** from A to B to make B depend on A. Click an edge, then press **Delete**, to remove it.
- Filter by milestone or hide finished work. **F** fits the graph to the view.
- Polls for file changes, so edits made by Claude or the CLI appear live.

## Develop

```sh
cd plugins/dag && uv run --group dev pytest -q
claude --plugin-dir plugins/dag                   # try the plugin from source
```
