---
id: yaml-format
title: Spec the YAML plan format
kind: decision
status: todo
deps: []
milestone: m5-yaml-storage
---

## Goal / acceptance

- `plugins/dag/docs/format.md` specifies the format with examples, and the user has approved it before any implementation starts. It covers:
  - **Files:** which files are loaded (e.g. `.claude-dag/plan/**/*.yaml`) and their order. Ids are unique across all files, and references are bare ids, never file paths.
  - **Node syntax:** a node is a mapping keyed by its id. Fields use reserved keys (`title`, `kind`, `status`, `after`, `verify`, `body`, ...) and every other key is a child node, so no node may be named after a reserved key. A shorthand `id: Title` is allowed for leaves only. YAML can't give a key both a string value and children, so an earlier sketch that did this was invalid.
  - **What nesting means:** children of a milestone are its members; children of any other node depend on it. Decide whether a child of a member also belongs to the milestone (probably yes, the nearest milestone above it).
  - **`after:`:** extra deps, which may point to nodes in other files.
  - **`body:`:** a path to a markdown file, or a list of paths, resolved relative to the YAML file. Decide whether `file.md#heading` can point to one section of a shared doc. Decide where `dag_append` / `## Result` writes go when there are several bodies or none: which file, which default location, and whether `body:` is added to the YAML automatically.
  - **Placement:** which file a node added by a tool goes into (e.g. its milestone's file, else its first dep's file, else `plan/main.yaml`).
  - **Unchanged:** `log.md` and `layout.json` stay as they are.

## Notes

Open points to settle with the user:
- Indentation vs a chain of nodes listed one after another. Deep chains get very indented.
- Should status stay in the YAML (simple, but every status change edits a file the user also edits), or go in a separate machine-written state file?

## Result
