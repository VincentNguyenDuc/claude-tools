"""Node model and its markdown + YAML-frontmatter file format."""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from typing import Any

import yaml

KINDS = ("task", "milestone", "research", "decision", "test")
# Statuses that may be stored in a file. "ready" is derived (todo + all deps satisfied).
STATUSES = ("todo", "active", "blocked", "done", "failed", "dropped")
EFFECTIVE_STATUSES = ("todo", "ready", "active", "blocked", "done", "failed", "dropped")
SATISFIED = frozenset({"done", "dropped"})

ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
CORE_KEYS = ("id", "title", "kind", "status", "deps", "milestone", "verify")
DEFAULT_BODY = "## Goal / acceptance\n\n\n## Notes\n\n\n## Result\n"

_FRONTMATTER_RE = re.compile(r"\A---[ \t]*\n(.*?)^---[ \t]*$\n?(.*)\Z", re.S | re.M)


class DagError(ValueError):
    """A user-facing error: bad input or an invalid change to the graph."""


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:48].rstrip("-") or "node"


def as_id_list(value: Any) -> list[str]:
    """Accept a list or a comma-separated string of node ids."""
    if value is None or value == "":
        return []
    if isinstance(value, str):
        items = value.split(",")
    elif isinstance(value, (list, tuple)):
        items = value
    else:
        raise DagError(f"expected a list of node ids, got {value!r}")
    return [str(v).strip() for v in items if str(v).strip()]


def opt_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def norm_status(value: Any) -> str:
    status = str(value or "todo").strip().lower()
    return "todo" if status == "ready" else status


@dataclass
class Node:
    id: str
    title: str
    kind: str = "task"
    status: str = "todo"
    deps: list[str] = field(default_factory=list)
    milestone: str | None = None
    verify: str | None = None
    body: str = DEFAULT_BODY
    extra: dict[str, Any] = field(default_factory=dict)

    def copy(self) -> Node:
        return replace(self, deps=list(self.deps), extra=dict(self.extra))

    def problems(self) -> list[str]:
        """Problems visible from this node alone (references are checked by the graph)."""
        out = []
        if not ID_RE.match(self.id):
            out.append(f"{self.id}: invalid id (use lowercase letters, digits and dashes, max 64)")
        if not self.title.strip():
            out.append(f"{self.id}: empty title")
        if self.kind not in KINDS:
            out.append(f"{self.id}: unknown kind {self.kind!r} (one of: {', '.join(KINDS)})")
        if self.status not in STATUSES:
            out.append(f"{self.id}: unknown status {self.status!r} (one of: {', '.join(STATUSES)})")
        if self.id in self.deps:
            out.append(f"{self.id}: depends on itself")
        if len(set(self.deps)) != len(self.deps):
            out.append(f"{self.id}: duplicate deps")
        if self.milestone == self.id:
            out.append(f"{self.id}: is its own milestone")
        return out

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "kind": self.kind,
            "status": self.status,
            "deps": list(self.deps),
            "milestone": self.milestone,
            "verify": self.verify,
            "body": self.body,
            "extra": dict(self.extra),
        }

    def to_markdown(self) -> str:
        meta: dict[str, Any] = {
            "id": self.id,
            "title": self.title,
            "kind": self.kind,
            "status": self.status,
            "deps": list(self.deps),
        }
        if self.milestone:
            meta["milestone"] = self.milestone
        if self.verify:
            meta["verify"] = self.verify
        for key, value in self.extra.items():
            meta.setdefault(key, value)
        front = yaml.safe_dump(
            meta, sort_keys=False, default_flow_style=None, allow_unicode=True, width=10_000
        )
        body = self.body.strip("\n")
        return f"---\n{front}---\n\n{body}\n" if body else f"---\n{front}---\n"

    @classmethod
    def from_markdown(cls, text: str, fallback_id: str) -> Node:
        text = text.replace("\r\n", "\n")
        meta: Any = {}
        body = text
        match = _FRONTMATTER_RE.match(text)
        if match:
            try:
                meta = yaml.safe_load(match.group(1)) or {}
            except yaml.YAMLError as exc:
                raise DagError(f"bad frontmatter: {exc}") from None
            body = match.group(2)
        if not isinstance(meta, dict):
            raise DagError("frontmatter must be a YAML mapping")
        node_id = str(meta.get("id") or fallback_id).strip()
        return cls(
            id=node_id,
            title=str(meta.get("title") or node_id),
            kind=str(meta.get("kind") or "task").strip().lower(),
            status=norm_status(meta.get("status")),
            deps=as_id_list(meta.get("deps")),
            milestone=opt_str(meta.get("milestone")),
            verify=opt_str(meta.get("verify")),
            body=body.lstrip("\n"),
            extra={k: v for k, v in meta.items() if k not in CORE_KEYS},
        )
