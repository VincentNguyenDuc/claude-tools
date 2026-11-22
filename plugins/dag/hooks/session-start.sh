#!/usr/bin/env bash
# SessionStart hook: if the project has a .claude-dag/, print a short plan summary.
# Stdout becomes session context. Silent (exit 0) when there is no plan or on any error.
set -u
dir="${CLAUDE_PROJECT_DIR:-$PWD}"
while [ "$dir" != "/" ] && [ ! -d "$dir/.claude-dag" ]; do
  dir="$(dirname "$dir")"
done
[ -d "$dir/.claude-dag" ] || exit 0
unset VIRTUAL_ENV
root="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
summary="$(uv run --quiet --project "$root" claude-dag -C "$dir" summary 2>/dev/null | head -n 40)" || exit 0
[ -n "$summary" ] || exit 0
cat <<MSG
This project has a planning DAG in $dir/.claude-dag/ (dag plugin). Use the dag_* MCP tools
to read or change it; /dag:next works the next ready node, /dag:replan revises the plan.
$summary
MSG
