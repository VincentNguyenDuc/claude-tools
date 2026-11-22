"""Node positions for the web UI, kept in .claude-dag/layout.json.

Positions live apart from the node files so that dragging a node doesn't touch
the plan itself (no git noise, no change token bump for the node files).
The file is optional: missing or corrupt means "no saved positions".

    {"positions": {"<node id>": {"x": 120.0, "y": 40.0}, ...}}
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .model import DagError

LAYOUT_FILE = "layout.json"

Positions = dict[str, dict[str, float]]


def layout_path(dag_dir: Path) -> Path:
    return Path(dag_dir) / LAYOUT_FILE


def layout_version(dag_dir: Path) -> str:
    """Change token for layout.json, separate from the node files' version."""
    path = layout_path(dag_dir)
    try:
        st = path.stat()
    except OSError:
        return "0"
    return hashlib.sha1(f"{st.st_mtime_ns}:{st.st_size}".encode()).hexdigest()[:16]


def _point(value: Any) -> dict[str, float] | None:
    if not isinstance(value, dict):
        return None
    try:
        x, y = float(value["x"]), float(value["y"])
    except (KeyError, TypeError, ValueError):
        return None
    if not (math.isfinite(x) and math.isfinite(y)):
        return None
    return {"x": round(x, 1), "y": round(y, 1)}


def read_layout(dag_dir: Path, known_ids: Iterable[str] | None = None) -> Positions:
    """Saved positions, minus malformed entries and (if given) ids not in known_ids."""
    try:
        data = json.loads(layout_path(dag_dir).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    raw = data.get("positions") if isinstance(data, dict) else None
    if not isinstance(raw, dict):
        return {}
    known = None if known_ids is None else set(known_ids)
    out: Positions = {}
    for node_id, value in raw.items():
        point = _point(value)
        if point is not None and (known is None or node_id in known):
            out[str(node_id)] = point
    return out


def _write(dag_dir: Path, positions: Positions) -> None:
    from .graph import _atomic_write  # local import: graph imports this module

    text = json.dumps({"positions": dict(sorted(positions.items()))}, indent=1) + "\n"
    _atomic_write(layout_path(dag_dir), text)


def save_layout(
    dag_dir: Path, update: Any, known_ids: Iterable[str], *, replace: bool = False
) -> Positions:
    """Merge (or with replace=True, replace) positions and write the file atomically.

    In merge mode a null value removes that id. Ids that aren't nodes are dropped.
    """
    if not isinstance(update, dict):
        raise DagError("positions must be an object of {id: {x, y}}")
    known = set(known_ids)
    positions = {} if replace else read_layout(dag_dir, known)
    for node_id, value in update.items():
        if value is None and not replace:
            positions.pop(node_id, None)
            continue
        point = _point(value)
        if point is None:
            raise DagError(f"bad position for {node_id!r}: expected {{x, y}} numbers")
        if node_id in known:
            positions[node_id] = point
    _write(dag_dir, positions)
    return positions


def rename_in_layout(dag_dir: Path, old_id: str, new_id: str) -> None:
    positions = read_layout(dag_dir)
    if old_id in positions:
        positions[new_id] = positions.pop(old_id)
        _write(dag_dir, positions)


def drop_from_layout(dag_dir: Path, node_id: str) -> None:
    positions = read_layout(dag_dir)
    if positions.pop(node_id, None) is not None:
        _write(dag_dir, positions)
