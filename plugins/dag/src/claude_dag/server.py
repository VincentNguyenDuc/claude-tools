"""Local web UI server: a JSON API over the graph plus a single static page.

Binds to 127.0.0.1 only. Requests must carry a localhost Host header (blocks DNS
rebinding), mutating requests must be JSON (forces a CORS preflight that is never
answered) and any Origin must be localhost (blocks cross-site form posts).
"""

from __future__ import annotations

import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from .graph import EDITABLE, Graph, dir_version
from .layout import layout_version, read_layout, save_layout
from .model import DagError

LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
ADD_FIELDS = {"id", "kind", "status", "deps", "milestone", "verify", "body"}
MAX_BODY = 2_000_000
_WRITE_LOCK = threading.Lock()


def _node_json(node: Any) -> dict[str, Any]:
    return {**node.to_dict(), "rev": node.revision()}


def _hostname(host_header: str) -> str:
    host = host_header.strip().lower()
    if host.startswith("["):
        return host[1:].split("]", 1)[0]
    return host.rsplit(":", 1)[0]


class Handler(BaseHTTPRequestHandler):
    dag_dir: Path  # set by make_server
    server_version = "claude-dag"

    def log_message(self, format: str, *args: Any) -> None:  # quiet
        pass

    # ------------------------------------------------------------- helpers

    def _allowed(self) -> bool:
        if _hostname(self.headers.get("Host", "")) not in LOCAL_HOSTS:
            return False
        origin = self.headers.get("Origin")
        return not origin or urlparse(origin).hostname in LOCAL_HOSTS

    def _send(self, code: int, payload: Any, ctype: str = "application/json") -> None:
        data = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", f"{ctype}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def _json_body(self) -> dict[str, Any]:
        ctype = self.headers.get("Content-Type", "").split(";")[0].strip().lower()
        if ctype != "application/json":
            raise DagError("expected Content-Type: application/json")
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            raise DagError("request too large")
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError as exc:
            raise DagError(f"bad JSON: {exc}") from None
        if not isinstance(data, dict):
            raise DagError("expected a JSON object")
        return data

    # ------------------------------------------------------------- routing

    def do_GET(self) -> None:
        self._route("GET")

    def do_POST(self) -> None:
        self._route("POST")

    def do_PATCH(self) -> None:
        self._route("PATCH")

    def do_PUT(self) -> None:
        self._route("PUT")

    def do_DELETE(self) -> None:
        self._route("DELETE")

    def _route(self, method: str) -> None:
        if not self._allowed():
            self._send(403, {"error": "forbidden"})
            return
        url = urlparse(self.path)
        parts = [unquote(p) for p in url.path.split("/") if p]
        try:
            if method == "GET":
                self._get(parts)
            else:
                with _WRITE_LOCK:
                    self._mutate(method, parts, url.query)
        except DagError as exc:
            self._send(400, {"error": str(exc)})

    def _get(self, parts: list[str]) -> None:
        if parts in ([], ["index.html"]):
            page = files("claude_dag").joinpath("static/index.html").read_bytes()
            self._send(200, page, "text/html")
        elif parts == ["api", "graph"]:
            self._send(200, Graph(self.dag_dir).to_json())
        elif parts == ["api", "version"]:
            self._send(200, {"version": dir_version(self.dag_dir), "layout": layout_version(self.dag_dir)})
        elif parts == ["api", "layout"]:
            positions = read_layout(self.dag_dir, Graph(self.dag_dir).nodes)
            self._send(200, {"positions": positions, "version": layout_version(self.dag_dir)})
        else:
            self._send(404, {"error": "not found"})

    def _mutate(self, method: str, parts: list[str], query: str) -> None:
        graph = Graph(self.dag_dir)  # fresh read: files may have changed on disk
        if method == "POST" and parts == ["api", "nodes"]:
            body = self._json_body()
            title = body.pop("title", "")
            unknown = set(body) - ADD_FIELDS
            if unknown:
                raise DagError(f"unknown field(s): {', '.join(sorted(unknown))}")
            node = graph.add(title, **body)
            self._send(201, {"node": _node_json(node)})
        elif method == "PATCH" and len(parts) == 3 and parts[:2] == ["api", "nodes"]:
            body = self._json_body()
            base_rev = body.pop("base_rev", None)
            unknown = set(body) - EDITABLE - {"id"}
            if unknown:
                raise DagError(f"cannot edit field(s): {', '.join(sorted(unknown))}")
            # Optional optimistic check: the client says which revision it edited.
            # Without base_rev the last writer wins (CLI/MCP-style callers).
            current = graph.get(parts[2])
            if base_rev is not None and str(base_rev) != current.revision():
                self._send(409, {"error": "node changed on disk since you opened it", "node": _node_json(current)})
                return
            node = graph.update(parts[2], **body)
            self._send(200, {"node": _node_json(node)})
        elif method == "DELETE" and len(parts) == 3 and parts[:2] == ["api", "nodes"]:
            force = parse_qs(query).get("force", ["0"])[0] in ("1", "true")
            graph.remove(parts[2], force=force)
            self._send(200, {"ok": True})
        elif method == "PUT" and parts == ["api", "layout"]:
            body = self._json_body()
            unknown = set(body) - {"positions", "replace"}
            if unknown:
                raise DagError(f"unknown field(s): {', '.join(sorted(unknown))}")
            positions = save_layout(
                self.dag_dir, body.get("positions", {}), graph.nodes, replace=bool(body.get("replace"))
            )
            self._send(200, {"positions": positions, "version": layout_version(self.dag_dir)})
        elif parts == ["api", "edges"] and method in ("POST", "DELETE"):
            body = self._json_body()
            src, dst = str(body.get("from", "")), str(body.get("to", ""))
            (graph.link if method == "POST" else graph.unlink)(src, dst)
            self._send(200, {"ok": True})
        else:
            self._send(404, {"error": "not found"})


def make_server(dag_dir: Path, port: int = 8765) -> ThreadingHTTPServer:
    handler = type("BoundHandler", (Handler,), {"dag_dir": Path(dag_dir)})
    return ThreadingHTTPServer(("127.0.0.1", port), handler)


def serve(dag_dir: Path, port: int = 8765, open_browser: bool = False) -> None:
    httpd = make_server(dag_dir, port)
    url = f"http://127.0.0.1:{httpd.server_address[1]}/"
    print(f"claude-dag: {dag_dir} -> {url}  (Ctrl+C to stop)", flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
