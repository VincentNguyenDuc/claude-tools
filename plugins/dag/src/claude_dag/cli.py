"""claude-dag command line."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from .graph import DIR_NAME, Graph, git_toplevel
from .model import KINDS, STATUSES, DagError

SYMBOL = {
    "done": "✓", "ready": "▶", "active": "●", "todo": "○",
    "blocked": "■", "failed": "✗", "dropped": "–",
}


def _start(args: argparse.Namespace) -> Path | None:
    return Path(args.dir) if args.dir else None


def _graph(args: argparse.Namespace) -> Graph:
    return Graph.open(_start(args))


def _read_body(args: argparse.Namespace) -> str | None:
    if getattr(args, "body_file", None):
        if args.body_file == "-":
            return sys.stdin.read()
        return Path(args.body_file).read_text(encoding="utf-8")
    return getattr(args, "body", None)


def _print_json(obj) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------- commands

def cmd_init(args):
    if args.path:
        root = Path(args.path)
    else:
        start = _start(args) or Path.cwd()
        root = git_toplevel(start) or start
    root = root.resolve()
    existed = (root / DIR_NAME).is_dir()
    graph = Graph.init(root)
    print(f"{'already initialized' if existed else 'initialized'}: {graph.dir}")


def cmd_add(args):
    graph = _graph(args)
    node = graph.add(
        args.title, id=args.id, kind=args.kind, status=args.status, deps=args.deps,
        milestone=args.milestone, verify=args.verify, body=_read_body(args),
    )
    print(f"added {node.id}  ({graph.path_for(node.id).relative_to(graph.project_root)})")


def cmd_edit(args):
    graph = _graph(args)
    node = graph.get(args.id)
    fields = {}
    for key in ("title", "kind", "status", "milestone", "verify"):
        value = getattr(args, key)
        if value is not None:
            fields[key] = value
    deps = list(node.deps) if args.deps is None else [d.strip() for d in args.deps.split(",") if d.strip()]
    for dep in args.add_dep or []:
        if dep not in deps:
            deps.append(dep)
    for dep in args.rm_dep or []:
        if dep not in deps:
            raise DagError(f"{args.id} does not depend on {dep}")
        deps.remove(dep)
    if deps != node.deps:
        fields["deps"] = deps
    body = _read_body(args)
    if body is not None:
        fields["body"] = body
    if args.rename:
        fields["id"] = args.rename
    if not fields:
        raise DagError("nothing to change (see `claude-dag edit --help`)")
    node = graph.update(args.id, **fields)
    print(f"updated {node.id}")


def cmd_append(args):
    text = sys.stdin.read() if args.text == "-" else args.text
    _graph(args).append(args.id, text, args.section)
    print(f"appended to {args.id} ## {args.section}")


def cmd_import(args):
    raw = sys.stdin.read() if args.file == "-" else Path(args.file).read_text(encoding="utf-8")
    try:
        specs = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise DagError(f"bad YAML/JSON: {exc}") from None
    if isinstance(specs, dict):
        specs = specs.get("nodes")
    if not isinstance(specs, list):
        raise DagError("expected a list of nodes (or {nodes: [...]})")
    added = _graph(args).add_many(specs)
    print(f"added {len(added)} nodes: {', '.join(n.id for n in added)}")


def cmd_rm(args):
    _graph(args).remove(args.id, force=args.force)
    print(f"removed {args.id}")


def cmd_link(args):
    _graph(args).link(args.src, args.dst)
    print(f"{args.dst} now depends on {args.src}")


def cmd_unlink(args):
    _graph(args).unlink(args.src, args.dst)
    print(f"{args.dst} no longer depends on {args.src}")


def _set(args, status):
    graph = _graph(args)
    graph.update(args.id, status=status)
    print(f"{args.id}: {graph.statuses()[args.id]}")


def cmd_set(args):
    _set(args, args.status)


def cmd_verify(args):
    graph = _graph(args)
    ok, output = graph.verify(args.id, timeout=args.timeout)
    tail = output.strip().splitlines()[-args.tail:] if args.tail else []
    if tail:
        print("\n".join(tail))
    print(f"{'PASS' if ok else 'FAIL'}: {args.id} -> {'done' if ok else 'failed'}")
    return 0 if ok else 1


def cmd_show(args):
    graph = _graph(args)
    node = graph.get(args.id)
    status = graph.statuses()[node.id]
    if args.json:
        _print_json({**node.to_dict(), "effective_status": status,
                     "dependents": graph.dependents(node.id), "members": graph.members(node.id)})
        return
    print(f"# {SYMBOL.get(status, '?')} {status}  —  {graph.path_for(node.id)}")
    print(node.to_markdown(), end="")


def _rows(graph: Graph, args) -> list[str]:
    st = graph.statuses()
    ids = graph.topo_order()
    if args.status:
        ids = [i for i in ids if st[i] == args.status]
    if args.milestone:
        ids = [i for i in ids if i == args.milestone or graph.nodes[i].milestone == args.milestone]
    return ids


def cmd_list(args):
    graph = _graph(args)
    st = graph.statuses()
    ids = _rows(graph, args)
    if args.json:
        _print_json([{**graph.nodes[i].to_dict(), "effective_status": st[i]} for i in ids])
        return
    if not ids:
        print("(no nodes)")
        return
    width = max(len(i) for i in ids)
    for i in ids:
        node = graph.nodes[i]
        deps = f"  <- {', '.join(node.deps)}" if node.deps else ""
        ms = f"  [{node.milestone}]" if node.milestone else ""
        title = f"◆ {node.title}" if node.kind == "milestone" else node.title
        print(f"{SYMBOL.get(st[i], '?')} {st[i]:<8} {i:<{width}}  {node.kind:<9} {title}{ms}{deps}")


def cmd_ready(args):
    graph = _graph(args)
    nodes = [n for n in graph.ready() if n.kind != "milestone"]
    if args.json:
        _print_json([n.to_dict() for n in nodes])
        return
    if not nodes:
        print("(nothing ready)")
    for node in nodes:
        verify = f"  [verify: {node.verify}]" if node.verify else ""
        print(f"▶ {node.id}: {node.title}{verify}")


def cmd_summary(args):
    print(_graph(args).summary())


def cmd_validate(args):
    errors = _graph(args).validate()
    for err in errors:
        print(f"- {err}")
    if errors:
        return 1
    print("ok")


def cmd_log(args):
    _graph(args).log(" ".join(args.message))


def cmd_serve(args):
    from .server import serve

    serve(_graph(args).dir, port=args.port, open_browser=args.open)


# ------------------------------------------------------------------ parser

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="claude-dag",
        description=f"Planning DAG stored as markdown files in {DIR_NAME}/ of a project.",
    )
    p.add_argument("-C", "--dir", help="directory to search upward from (default: cwd)")
    sub = p.add_subparsers(dest="cmd", required=True, metavar="COMMAND")

    def cmd(name, func, help_):
        sp = sub.add_parser(name, help=help_, description=help_)
        sp.set_defaults(func=func)
        return sp

    sp = cmd("init", cmd_init, f"create {DIR_NAME}/ (in the git root by default)")
    sp.add_argument("path", nargs="?")

    sp = cmd("add", cmd_add, "add a node")
    sp.add_argument("title")
    sp.add_argument("--id", help="node id (default: slug of the title)")
    sp.add_argument("-k", "--kind", default="task", choices=KINDS)
    sp.add_argument("-s", "--status", default="todo", choices=STATUSES)
    sp.add_argument("-d", "--deps", default="", help="comma-separated ids this node depends on")
    sp.add_argument("-m", "--milestone", help="milestone this node belongs to")
    sp.add_argument("-v", "--verify", help="shell command that must pass for the node to be done")
    sp.add_argument("--body", help="markdown body (default: template)")
    sp.add_argument("--body-file", help="read markdown body from a file ('-' for stdin)")

    sp = cmd("edit", cmd_edit, "change a node's fields")
    sp.add_argument("id")
    sp.add_argument("--title")
    sp.add_argument("-k", "--kind", choices=KINDS)
    sp.add_argument("-s", "--status", choices=STATUSES)
    sp.add_argument("-d", "--deps", help="replace deps (comma-separated; '' clears)")
    sp.add_argument("--add-dep", action="append", metavar="ID")
    sp.add_argument("--rm-dep", action="append", metavar="ID")
    sp.add_argument("-m", "--milestone", help="set milestone ('' clears)")
    sp.add_argument("-v", "--verify", help="set verify command ('' clears)")
    sp.add_argument("--body")
    sp.add_argument("--body-file")
    sp.add_argument("--rename", metavar="NEW_ID", help="rename the node and update references")

    sp = cmd("append", cmd_append, "append markdown to a section of a node's body")
    sp.add_argument("id")
    sp.add_argument("text", help="markdown text ('-' for stdin)")
    sp.add_argument("--section", default="Result")

    sp = cmd("import", cmd_import, "add many nodes at once from YAML/JSON (all or nothing)")
    sp.add_argument("file", help="file with a list of {title, id?, kind?, deps?, ...} ('-' for stdin)")

    sp = cmd("rm", cmd_rm, "remove a node")
    sp.add_argument("id")
    sp.add_argument("-f", "--force", action="store_true", help="also drop references to it")

    sp = cmd("link", cmd_link, "add edge SRC -> DST (DST depends on SRC)")
    sp.add_argument("src")
    sp.add_argument("dst")

    sp = cmd("unlink", cmd_unlink, "remove edge SRC -> DST")
    sp.add_argument("src")
    sp.add_argument("dst")

    sp = cmd("set", cmd_set, "set a node's stored status")
    sp.add_argument("id")
    sp.add_argument("status", choices=STATUSES)
    for name, status in (("start", "active"), ("done", "done"), ("fail", "failed"), ("drop", "dropped")):
        sp = cmd(name, lambda a, s=status: _set(a, s), f"set status to {status}")
        sp.add_argument("id")

    sp = cmd("verify", cmd_verify, "run the node's verify command; mark done (pass) or failed")
    sp.add_argument("id")
    sp.add_argument("--timeout", type=float, default=600)
    sp.add_argument("--tail", type=int, default=20, help="lines of output to show (0 = none)")

    sp = cmd("show", cmd_show, "print a node")
    sp.add_argument("id")
    sp.add_argument("--json", action="store_true")

    sp = cmd("list", cmd_list, "list nodes in dependency order")
    sp.add_argument("-s", "--status", choices=("todo", "ready", *STATUSES[1:]))
    sp.add_argument("-m", "--milestone")
    sp.add_argument("--json", action="store_true")

    sp = cmd("ready", cmd_ready, "nodes whose dependencies are all done")
    sp.add_argument("--json", action="store_true")

    cmd("summary", cmd_summary, "progress overview")
    cmd("validate", cmd_validate, "check for missing references, bad fields and cycles")

    sp = cmd("log", cmd_log, f"append a line to {DIR_NAME}/log.md")
    sp.add_argument("message", nargs="+")

    sp = cmd("serve", cmd_serve, "open the web UI (localhost only)")
    sp.add_argument("-p", "--port", type=int, default=8765)
    sp.add_argument("-o", "--open", action="store_true", help="open a browser")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args) or 0
    except DagError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130
