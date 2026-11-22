# dag

A planning DAG for long-running work. The plan lives as markdown files in the
project's `.claude-dag/`, versioned with the code. You and Claude both read and
edit it, through the CLI, the web UI, or by editing the files directly.

Status: **M1**, which covers the file format, CLI and web UI. Claude-facing skills and an MCP server come next
(see this repo's own `.claude-dag/`).

## Install the CLI

```sh
uv tool install --editable ~/dev/PERSONAL/claude-tools/plugins/dag   # puts `claude-dag` on PATH
# or, without installing:
uv run --project ~/dev/PERSONAL/claude-tools/plugins/dag claude-dag --help
```

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
```
