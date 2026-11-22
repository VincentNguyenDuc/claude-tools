"""MCP server exposing the planning DAG as tools (stdio transport).

The project is found by searching upward from $CLAUDE_PROJECT_DIR (set by Claude
Code) or the working directory for a .claude-dag/ directory.
"""

from __future__ import annotations

import functools
import os
import threading
import webbrowser
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from . import __version__
from .graph import DIR_NAME, Graph, git_toplevel
from .model import DagError

INSTRUCTIONS = f"""\
Planning DAG stored as markdown files in the project's {DIR_NAME}/ directory.
Each node has: id, title, kind (task|milestone|research|decision|test), status
(todo|active|blocked|done|failed|dropped), deps (ids it waits on), optional
milestone (a milestone node it belongs to), optional verify (shell command that
must pass), and a markdown body (## Goal / acceptance, ## Notes, ## Result).
"ready" is derived: a todo node whose deps are all done or dropped. Milestones
are derived from their deps and members. The graph rejects cycles.
Start with dag_summary. Change nodes only through these tools.
"""

server = MCPServer("dag", instructions=INSTRUCTIONS, version=__version__)
_ui_urls: dict[str, str] = {}


def tool(fn):
    """Register a tool; DagError becomes a ToolError so the model sees the message."""

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return fn(*args, **kwargs)
        except DagError as exc:
            raise ToolError(str(exc)) from None

    return server.tool()(wrapper)


def _start() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def _graph() -> Graph:
    return Graph.open(_start())


def _brief(graph: Graph, statuses: dict[str, str], node_id: str) -> dict[str, Any]:
    node = graph.nodes[node_id]
    out: dict[str, Any] = {"id": node.id, "title": node.title, "kind": node.kind, "status": statuses[node.id]}
    if node.deps:
        out["deps"] = node.deps
    if node.milestone:
        out["milestone"] = node.milestone
    if node.verify:
        out["verify"] = node.verify
    return out


def _full(graph: Graph, node_id: str) -> dict[str, Any]:
    node = graph.get(node_id)
    return {
        **node.to_dict(),
        "effective_status": graph.statuses()[node.id],
        "dependents": graph.dependents(node.id),
        "members": graph.members(node.id),
        "file": str(graph.path_for(node.id)),
    }


@tool
def dag_summary() -> str:
    """Progress overview: counts, milestones, and the active/ready/failed/blocked nodes."""
    graph = _graph()
    return f"{graph.dir}\n{graph.summary()}"


@tool
def dag_list(status: str | None = None, milestone: str | None = None) -> list[dict[str, Any]]:
    """List nodes in dependency order (no bodies). Optional filters: effective status, milestone id."""
    graph = _graph()
    st = graph.statuses()
    ids = graph.topo_order()
    if status:
        ids = [i for i in ids if st[i] == status]
    if milestone:
        ids = [i for i in ids if i == milestone or graph.nodes[i].milestone == milestone]
    return [_brief(graph, st, i) for i in ids]


@tool
def dag_show(id: str) -> dict[str, Any]:
    """Full node including its markdown body, effective status, dependents and members."""
    return _full(_graph(), id)


@tool
def dag_ready() -> list[dict[str, Any]]:
    """Nodes that can be worked on now (all deps done or dropped), with their bodies."""
    graph = _graph()
    return [_full(graph, n.id) for n in graph.ready() if n.kind != "milestone"]


@tool
def dag_add(
    title: str,
    id: str | None = None,
    kind: str = "task",
    deps: list[str] | None = None,
    milestone: str | None = None,
    verify: str | None = None,
    body: str | None = None,
) -> dict[str, Any]:
    """Add one node. id defaults to a slug of the title; body defaults to the section template."""
    graph = _graph()
    node = graph.add(title, id=id, kind=kind, deps=deps or [], milestone=milestone, verify=verify, body=body)
    return _full(graph, node.id)


@tool
def dag_add_many(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add several nodes atomically (all or nothing). Each item: {title, id?, kind?, deps?,
    milestone?, verify?, body?, status?}. Items may reference each other in any order.
    Use this to write a whole plan in one call."""
    graph = _graph()
    added = graph.add_many(nodes)
    st = graph.statuses()
    return [_brief(graph, st, n.id) for n in added]


@tool
def dag_update(
    id: str,
    title: str | None = None,
    kind: str | None = None,
    status: str | None = None,
    deps: list[str] | None = None,
    milestone: str | None = None,
    verify: str | None = None,
    body: str | None = None,
    new_id: str | None = None,
) -> dict[str, Any]:
    """Change fields of a node; omitted fields stay as they are. deps replaces the whole list.
    Pass "" for milestone or verify to clear it. new_id renames the node and updates references."""
    fields = {
        k: v
        for k, v in {"title": title, "kind": kind, "status": status, "deps": deps,
                     "milestone": milestone, "verify": verify, "body": body}.items()
        if v is not None
    }
    if new_id:
        fields["id"] = new_id
    if not fields:
        raise DagError("nothing to change")
    graph = _graph()
    node = graph.update(id, **fields)
    return _full(graph, node.id)


@tool
def dag_append(id: str, text: str, section: str = "Result") -> str:
    """Append markdown to a section of a node's body (Result, Notes, ...; created if missing).
    Use it to record outcomes, findings and decisions without rewriting the body."""
    graph = _graph()
    graph.append(id, text, section)
    return f"appended to {id} ## {section}"


@tool
def dag_link(src: str, dst: str) -> str:
    """Add a dependency edge src -> dst, meaning dst depends on src. Rejected if it creates a cycle."""
    _graph().link(src, dst)
    return f"{dst} now depends on {src}"


@tool
def dag_unlink(src: str, dst: str) -> str:
    """Remove the dependency edge src -> dst."""
    _graph().unlink(src, dst)
    return f"{dst} no longer depends on {src}"


@tool
def dag_remove(id: str, force: bool = False) -> str:
    """Delete a node. Prefer status "dropped", which keeps history. force=True also removes
    references to it from other nodes."""
    _graph().remove(id, force=force)
    return f"removed {id}"


@tool
def dag_verify(id: str, timeout_seconds: float = 600) -> dict[str, Any]:
    """Run the node's verify command (shell, in the project root). Pass marks it done, failure
    marks it failed; both are logged. Returns pass/fail and the tail of the output."""
    graph = _graph()
    command = graph.get(id).verify
    ok, output = graph.verify(id, timeout=timeout_seconds)
    lines = output.strip().splitlines()
    return {
        "id": id,
        "passed": ok,
        "status": "done" if ok else "failed",
        "command": command,
        "output_tail": "\n".join(lines[-60:]),
    }


@tool
def dag_log(message: str) -> str:
    """Append a line to .claude-dag/log.md (decisions, replans, notable events)."""
    _graph().log(message)
    return "logged"


@tool
def dag_validate() -> list[str]:
    """Problems in the graph: missing references, bad fields, cycles. Empty list means ok."""
    return _graph().validate()


@tool
def dag_init() -> str:
    """Create .claude-dag/ at the git root of the current project (or the project dir)."""
    start = _start()
    root = git_toplevel(start) or start
    existed = (root / DIR_NAME).is_dir()
    graph = Graph.init(root)
    return f"{'already initialized' if existed else 'initialized'}: {graph.dir}"


@tool
def dag_open_ui(open_browser: bool = False, port: int = 8765) -> str:
    """Start the local web UI for this project's graph (if not already running) and return its URL."""
    from .server import make_server

    graph = _graph()
    key = str(graph.dir)
    if key not in _ui_urls:
        try:
            httpd = make_server(graph.dir, port)
        except OSError:
            httpd = make_server(graph.dir, 0)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        _ui_urls[key] = f"http://127.0.0.1:{httpd.server_address[1]}/"
    if open_browser:
        webbrowser.open(_ui_urls[key])
    return _ui_urls[key]


def main() -> None:
    server.run("stdio")


if __name__ == "__main__":
    main()
