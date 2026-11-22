"""The planning graph: loads .claude-dag/nodes/*.md, derives status, applies safe edits."""

from __future__ import annotations

import datetime
import hashlib
import heapq
import os
import re
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from .layout import drop_from_layout, rename_in_layout
from .model import (
    DEFAULT_BODY,
    EFFECTIVE_STATUSES,
    SATISFIED,
    DagError,
    Node,
    as_id_list,
    norm_status,
    opt_str,
    slugify,
)

DIR_NAME = ".claude-dag"
NODES_DIR = "nodes"
LOG_FILE = "log.md"
EDITABLE = frozenset({"title", "kind", "status", "deps", "milestone", "verify", "body"})
ADD_FIELDS = EDITABLE | {"id"}


def find_dag_dir(start: Path | None = None) -> Path | None:
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / DIR_NAME).is_dir():
            return candidate / DIR_NAME
    return None


def git_toplevel(start: Path) -> Path | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=start, capture_output=True, text=True, check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return Path(out.stdout.strip())


def dir_version(dag_dir: Path) -> str:
    """Cheap change token for the node files (used by the web UI to poll)."""
    digest = hashlib.sha1()
    nodes_dir = Path(dag_dir) / NODES_DIR
    if nodes_dir.is_dir():
        for path in sorted(nodes_dir.glob("*.md")):
            st = path.stat()
            digest.update(f"{path.name}:{st.st_mtime_ns}:{st.st_size};".encode())
    return digest.hexdigest()[:16]


def _atomic_write(path: Path, text: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


class Graph:
    def __init__(self, dag_dir: Path):
        self.dir = Path(dag_dir)
        self.nodes: dict[str, Node] = {}
        self.load_errors: list[str] = []
        self.reload()

    # ------------------------------------------------------------------ setup

    @classmethod
    def open(cls, start: Path | None = None) -> Graph:
        dag_dir = find_dag_dir(start)
        if dag_dir is None:
            where = start or Path.cwd()
            raise DagError(f"no {DIR_NAME}/ in {where} or its parents; run `claude-dag init`")
        return cls(dag_dir)

    @classmethod
    def init(cls, project_root: Path) -> Graph:
        dag_dir = Path(project_root) / DIR_NAME
        (dag_dir / NODES_DIR).mkdir(parents=True, exist_ok=True)
        log = dag_dir / LOG_FILE
        if not log.exists():
            log.write_text("# Log\n\n", encoding="utf-8")
        return cls(dag_dir)

    @property
    def project_root(self) -> Path:
        return self.dir.parent

    @property
    def nodes_dir(self) -> Path:
        return self.dir / NODES_DIR

    def path_for(self, node_id: str) -> Path:
        return self.nodes_dir / f"{node_id}.md"

    def reload(self) -> None:
        self.nodes, self.load_errors = {}, []
        if not self.nodes_dir.is_dir():
            return
        for path in sorted(self.nodes_dir.glob("*.md")):
            try:
                node = Node.from_markdown(path.read_text(encoding="utf-8"), path.stem)
            except (DagError, OSError, UnicodeDecodeError) as exc:
                self.load_errors.append(f"{path.name}: {exc}")
                continue
            if node.id != path.stem:
                # The file name is authoritative; the next save rewrites the id.
                self.load_errors.append(
                    f"{path.name}: id {node.id!r} does not match file name (using {path.stem!r})"
                )
                node.id = path.stem
            self.nodes[node.id] = node

    def version(self) -> str:
        return dir_version(self.dir)

    # -------------------------------------------------------------- structure

    def get(self, node_id: str) -> Node:
        try:
            return self.nodes[node_id]
        except KeyError:
            raise DagError(f"no node {node_id!r}") from None

    def members(self, milestone_id: str) -> list[str]:
        return [n.id for n in self.nodes.values() if n.milestone == milestone_id]

    def dependents(self, node_id: str) -> list[str]:
        return [n.id for n in self.nodes.values() if node_id in n.deps]

    def effective_deps(self, node_id: str) -> list[str]:
        """Explicit deps, plus a milestone's members (a milestone waits on its members)."""
        node = self.nodes[node_id]
        deps = [d for d in node.deps if d in self.nodes]
        if node.kind == "milestone":
            deps += [m for m in self.members(node_id) if m not in deps]
        return deps

    def find_cycle(self) -> list[str] | None:
        color: dict[str, int] = {}
        for start in self.nodes:
            if color.get(start):
                continue
            color[start] = 1
            path = [start]
            stack = [iter(self.effective_deps(start))]
            while stack:
                nxt = next(stack[-1], None)
                if nxt is None:
                    color[path.pop()] = 2
                    stack.pop()
                    continue
                state = color.get(nxt, 0)
                if state == 1:
                    return path[path.index(nxt):] + [nxt]
                if state == 0:
                    color[nxt] = 1
                    path.append(nxt)
                    stack.append(iter(self.effective_deps(nxt)))
        return None

    def topo_order(self) -> list[str]:
        """Dependencies first; ties broken by id. Nodes stuck in cycles go last."""
        indeg = {i: 0 for i in self.nodes}
        out: dict[str, list[str]] = {i: [] for i in self.nodes}
        for node_id in self.nodes:
            for dep in self.effective_deps(node_id):
                out[dep].append(node_id)
                indeg[node_id] += 1
        heap = [i for i, k in indeg.items() if k == 0]
        heapq.heapify(heap)
        order = []
        while heap:
            node_id = heapq.heappop(heap)
            order.append(node_id)
            for nxt in out[node_id]:
                indeg[nxt] -= 1
                if indeg[nxt] == 0:
                    heapq.heappush(heap, nxt)
        seen = set(order)
        return order + sorted(i for i in self.nodes if i not in seen)

    def statuses(self) -> dict[str, str]:
        """Effective status per node.

        - task-like nodes: stored status, except `todo` becomes `ready` once every
          dependency is done or dropped.
        - milestones: derived from their deps + members (done when all are satisfied).
        """
        memo: dict[str, str] = {}
        visiting: set[str] = set()

        def evaluate(node_id: str) -> str:
            if node_id in memo:
                return memo[node_id]
            if node_id in visiting:  # cycle: never ready
                return "blocked"
            visiting.add(node_id)
            node = self.nodes[node_id]
            dep_states = [evaluate(d) for d in self.effective_deps(node_id)]
            dangling = any(d not in self.nodes for d in node.deps)
            all_ok = not dangling and all(s in SATISFIED for s in dep_states)
            if node.status == "dropped":
                result = "dropped"
            elif node.kind == "milestone":
                if node.status == "blocked":
                    result = "blocked"
                elif not dep_states:
                    result = node.status if node.status in ("done", "active") else "todo"
                elif all_ok:
                    result = "done"
                elif "failed" in dep_states:
                    result = "failed"
                elif "active" in dep_states or any(
                    # A finished prerequisite (e.g. the previous milestone) is not
                    # progress on this one; only finished members are.
                    evaluate(m) == "done"
                    for m in (self.members(node_id) or node.deps)
                    if m in self.nodes
                ):
                    result = "active"
                else:
                    result = "todo"
            elif node.status != "todo":
                result = node.status
            else:
                result = "ready" if all_ok else "todo"
            visiting.discard(node_id)
            memo[node_id] = result
            return result

        for node_id in self.nodes:
            evaluate(node_id)
        return memo

    def ready(self) -> list[Node]:
        st = self.statuses()
        return [self.nodes[i] for i in self.topo_order() if st[i] == "ready"]

    def validate(self) -> list[str]:
        errors = list(self.load_errors)
        for node in self.nodes.values():
            errors += node.problems()
            for dep in node.deps:
                if dep not in self.nodes:
                    errors.append(f"{node.id}: depends on missing node {dep!r}")
            if node.milestone:
                ms = self.nodes.get(node.milestone)
                if ms is None:
                    errors.append(f"{node.id}: milestone {node.milestone!r} does not exist")
                elif ms.kind != "milestone":
                    errors.append(f"{node.id}: milestone {node.milestone!r} is a {ms.kind}, not a milestone")
        cycle = self.find_cycle()
        if cycle:
            errors.append("dependency cycle: " + " -> ".join(cycle))
        return errors

    # ---------------------------------------------------------------- editing

    def _check_refs(self, node: Node) -> None:
        missing = [d for d in node.deps if d not in self.nodes]
        if missing:
            raise DagError(f"{node.id}: unknown deps: {', '.join(missing)}")
        if node.milestone:
            ms = self.nodes.get(node.milestone)
            if ms is None:
                raise DagError(f"{node.id}: unknown milestone {node.milestone!r}")
            if ms.kind != "milestone" and ms.id != node.id:
                raise DagError(f"{node.id}: {node.milestone!r} is a {ms.kind}, not a milestone")

    def _commit(self, changed: list[Node], removed: tuple[str, ...] = ()) -> None:
        """Apply changes in memory, reject invalid nodes or new cycles, then write files."""
        had_cycle = self.find_cycle() is not None
        touched = [*removed, *(n.id for n in changed)]
        before = {node_id: self.nodes.get(node_id) for node_id in touched}
        for node_id in removed:
            self.nodes.pop(node_id, None)
        for node in changed:
            self.nodes[node.id] = node
        problems = [p for n in changed for p in n.problems()]
        cycle = None if had_cycle else self.find_cycle()
        if problems or cycle:
            for node_id, old in before.items():
                if old is None:
                    self.nodes.pop(node_id, None)
                else:
                    self.nodes[node_id] = old
            if problems:
                raise DagError("; ".join(problems))
            raise DagError("would create a dependency cycle: " + " -> ".join(cycle))
        self.nodes_dir.mkdir(parents=True, exist_ok=True)
        for node_id in removed:
            self.path_for(node_id).unlink(missing_ok=True)
        for node in changed:
            _atomic_write(self.path_for(node.id), node.to_markdown())

    def _unique_id(self, base: str, taken: set[str] | None = None) -> str:
        taken = set(self.nodes) if taken is None else taken
        candidate, n = base, 2
        while candidate in taken:
            candidate = f"{base}-{n}"
            n += 1
        return candidate

    @staticmethod
    def _build(spec: dict[str, Any], node_id: str) -> Node:
        unknown = set(spec) - ADD_FIELDS
        if unknown:
            raise DagError(f"unknown field(s): {', '.join(sorted(unknown))}")
        body = spec.get("body")
        return Node(
            id=node_id,
            title=str(spec.get("title") or "").strip(),
            kind=str(spec.get("kind") or "task").strip().lower(),
            status=norm_status(spec.get("status")),
            deps=as_id_list(spec.get("deps")),
            milestone=opt_str(spec.get("milestone")),
            verify=opt_str(spec.get("verify")),
            body=DEFAULT_BODY if body is None else str(body),
        )

    def add(self, title: str, **fields: Any) -> Node:
        """Add one node. Fields: id, kind, status, deps, milestone, verify, body."""
        return self.add_many([{**fields, "title": title}])[0]

    def add_many(self, specs: list[dict[str, Any]]) -> list[Node]:
        """Add several nodes atomically; they may reference each other in any order."""
        if not specs:
            raise DagError("no nodes given")
        taken = set(self.nodes)
        new: list[Node] = []
        for spec in specs:
            if not isinstance(spec, dict):
                raise DagError(f"expected a node object, got {spec!r}")
            title = str(spec.get("title") or "").strip()
            if not title:
                raise DagError("every node needs a title")
            node_id = opt_str(spec.get("id")) or self._unique_id(slugify(title), taken)
            if node_id in taken:
                raise DagError(f"node {node_id!r} already exists")
            taken.add(node_id)
            new.append(self._build(spec, node_id))
        kinds = {**{i: n.kind for i, n in self.nodes.items()}, **{n.id: n.kind for n in new}}
        for node in new:
            missing = [d for d in node.deps if d not in kinds]
            if missing:
                raise DagError(f"{node.id}: unknown deps: {', '.join(missing)}")
            if node.milestone and node.milestone != node.id:
                if node.milestone not in kinds:
                    raise DagError(f"{node.id}: unknown milestone {node.milestone!r}")
                if kinds[node.milestone] != "milestone":
                    raise DagError(f"{node.id}: {node.milestone!r} is a {kinds[node.milestone]}, not a milestone")
        self._commit(new)
        for node in new:
            self.log(f"added `{node.id}` ({node.kind}): {node.title}")
        return new

    def append(self, node_id: str, text: str, section: str = "Result") -> Node:
        """Append text to a `## <section>` of the node's body (created if missing)."""
        node = self.get(node_id).copy()
        text = (text or "").strip("\n")
        if not text.strip():
            raise DagError("nothing to append")
        section = section.strip() or "Result"
        lines = node.body.split("\n")
        header = re.compile(rf"^##\s+{re.escape(section)}\s*$", re.I)
        start = next((i for i, line in enumerate(lines) if header.match(line)), None)
        if start is None:
            node.body = f"{node.body.rstrip()}\n\n## {section}\n{text}\n".lstrip("\n")
        else:
            end = next((j for j in range(start + 1, len(lines)) if lines[j].startswith("## ")), len(lines))
            last = end
            while last > start + 1 and not lines[last - 1].strip():
                last -= 1
            gap = [""] if last > start + 1 else []
            tail = ([""] + lines[end:]) if end < len(lines) else []
            node.body = "\n".join(lines[:last] + gap + [text] + tail).rstrip("\n") + "\n"
        self._commit([node])
        return node

    def update(self, node_id: str, **fields: Any) -> Node:
        old = self.get(node_id)
        node = old.copy()
        new_id = opt_str(fields.pop("id", None))
        unknown = set(fields) - EDITABLE
        if unknown:
            raise DagError(f"cannot edit field(s): {', '.join(sorted(unknown))}")
        for key, value in fields.items():
            if key == "deps":
                value = as_id_list(value)
            elif key in ("milestone", "verify"):
                value = opt_str(value)
            elif key == "status":
                value = norm_status(value)
            elif key in ("title", "kind"):
                value = str(value or "").strip()
                if key == "kind":
                    value = value.lower()
            elif key == "body":
                value = "" if value is None else str(value)
            setattr(node, key, value)
        if old.kind == "milestone" and node.kind != "milestone" and self.members(node_id):
            raise DagError(f"{node_id} still has members; move them out before changing its kind")
        self._check_refs(node)

        changed, removed = [node], ()
        renamed = new_id is not None and new_id != node_id
        if renamed:
            if new_id in self.nodes:
                raise DagError(f"node {new_id!r} already exists")
            node.id = new_id
            removed = (node_id,)
            for other in self.nodes.values():
                if other.id == node_id or (node_id not in other.deps and other.milestone != node_id):
                    continue
                other = other.copy()
                other.deps = [new_id if d == node_id else d for d in other.deps]
                if other.milestone == node_id:
                    other.milestone = new_id
                changed.append(other)
        self._commit(changed, removed)
        if renamed:
            rename_in_layout(self.dir, node_id, new_id)
            self.log(f"renamed `{node_id}` -> `{new_id}`")
        if old.status != node.status:
            self.log(f"`{node.id}`: {old.status} -> {node.status}")
        return node

    def remove(self, node_id: str, *, force: bool = False) -> None:
        self.get(node_id)
        needed_by = self.dependents(node_id) + self.members(node_id)
        if needed_by and not force:
            raise DagError(
                f"{node_id} is referenced by: {', '.join(sorted(set(needed_by)))} "
                "(use --force to remove it and those references)"
            )
        changed = []
        for other in self.nodes.values():
            if other.id == node_id or (node_id not in other.deps and other.milestone != node_id):
                continue
            other = other.copy()
            other.deps = [d for d in other.deps if d != node_id]
            if other.milestone == node_id:
                other.milestone = None
            changed.append(other)
        self._commit(changed, (node_id,))
        drop_from_layout(self.dir, node_id)
        self.log(f"removed `{node_id}`")

    def link(self, src: str, dst: str) -> Node:
        """Make `dst` depend on `src` (edge src -> dst)."""
        self.get(src)
        node = self.get(dst).copy()
        if src == dst:
            raise DagError("a node cannot depend on itself")
        if src in node.deps:
            return node
        node.deps.append(src)
        self._commit([node])
        return node

    def unlink(self, src: str, dst: str) -> Node:
        node = self.get(dst).copy()
        if src not in node.deps:
            raise DagError(f"{dst} does not depend on {src}")
        node.deps.remove(src)
        self._commit([node])
        return node

    def verify(self, node_id: str, timeout: float = 600) -> tuple[bool, str]:
        """Run the node's verify command in the project root; mark done or failed."""
        node = self.get(node_id)
        if not node.verify:
            raise DagError(f"{node_id} has no verify command (set one, or mark it done directly)")
        try:
            proc = subprocess.run(
                node.verify, shell=True, cwd=self.project_root,
                capture_output=True, text=True, timeout=timeout,
            )
            ok, output, detail = proc.returncode == 0, proc.stdout + proc.stderr, f"exit {proc.returncode}"
        except subprocess.TimeoutExpired as exc:
            def _text(b: Any) -> str:
                return b.decode(errors="replace") if isinstance(b, bytes) else (b or "")
            ok, output, detail = False, _text(exc.stdout) + _text(exc.stderr), f"timed out after {timeout:g}s"
        self.update(node_id, status="done" if ok else "failed")
        self.log(f"verify `{node_id}`: {'pass' if ok else 'FAIL'} ({detail}) — `{node.verify}`")
        return ok, output

    def log(self, message: str) -> None:
        path = self.dir / LOG_FILE
        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        new = not path.exists()
        with path.open("a", encoding="utf-8") as fh:
            if new:
                fh.write("# Log\n\n")
            fh.write(f"- {stamp} — {message.strip()}\n")

    # ---------------------------------------------------------------- reports

    def to_json(self) -> dict[str, Any]:
        st = self.statuses()
        return {
            "root": str(self.project_root),
            "version": self.version(),
            "errors": self.validate(),
            "default_body": DEFAULT_BODY,
            "nodes": [
                {**self.nodes[i].to_dict(), "rev": self.nodes[i].revision(), "effective_status": st[i]}
                for i in self.topo_order()
            ],
        }

    def summary(self) -> str:
        st = self.statuses()
        order = self.topo_order()
        counts = Counter(st.values())
        parts = [f"{counts[s]} {s}" for s in EFFECTIVE_STATUSES if counts[s]]
        lines = [f"{len(self.nodes)} nodes" + (": " + ", ".join(parts) if parts else "")]
        milestones = [i for i in order if self.nodes[i].kind == "milestone"]
        if milestones:
            lines.append("Milestones:")
            for ms in milestones:
                deps = self.effective_deps(ms)
                done = sum(st[d] in SATISFIED for d in deps)
                lines.append(f"  ◆ {ms} — {self.nodes[ms].title} [{done}/{len(deps)}] {st[ms]}")
        for label, key in (("Active", "active"), ("Ready", "ready"), ("Failed", "failed"), ("Blocked", "blocked")):
            items = [i for i in order if st[i] == key and self.nodes[i].kind != "milestone"]
            if items:
                lines.append(f"{label}:")
                lines += [f"  - {i}: {self.nodes[i].title}" for i in items]
        errors = self.validate()
        if errors:
            lines.append(f"Problems: {len(errors)} (run `claude-dag validate`)")
        return "\n".join(lines)
