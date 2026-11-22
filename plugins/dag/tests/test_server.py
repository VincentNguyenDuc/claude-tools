import http.client
import json
import threading

import pytest

from claude_dag.graph import Graph
from claude_dag.server import make_server


@pytest.fixture
def server(tmp_path):
    Graph.init(tmp_path)
    httpd = make_server(tmp_path / ".claude-dag", port=0)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield httpd.server_address[1], tmp_path / ".claude-dag"
    httpd.shutdown()
    httpd.server_close()


def request(port, method, path, body=None, headers=None):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    hdrs = {"Content-Type": "application/json"} if body is not None else {}
    hdrs.update(headers or {})
    conn.request(method, path, body=None if body is None else json.dumps(body), headers=hdrs)
    res = conn.getresponse()
    data = res.read()
    conn.close()
    try:
        return res.status, json.loads(data)
    except json.JSONDecodeError:
        return res.status, data


def test_index_and_graph(server):
    port, _ = server
    status, page = request(port, "GET", "/")
    assert status == 200 and b"<title>claude-dag</title>" in page
    status, data = request(port, "GET", "/api/graph")
    assert status == 200 and data["nodes"] == [] and data["errors"] == []


def test_crud_and_edges(server):
    port, dag_dir = server
    assert request(port, "POST", "/api/nodes", {"title": "A", "id": "a"})[0] == 201
    assert request(port, "POST", "/api/nodes", {"title": "B", "id": "b"})[0] == 201
    assert request(port, "POST", "/api/edges", {"from": "a", "to": "b"})[0] == 200
    status, data = request(port, "POST", "/api/edges", {"from": "b", "to": "a"})
    assert status == 400 and "cycle" in data["error"]
    v1 = request(port, "GET", "/api/version")[1]["version"]
    status, data = request(port, "PATCH", "/api/nodes/a", {"status": "done", "body": "notes"})
    assert status == 200 and data["node"]["status"] == "done"
    assert request(port, "GET", "/api/version")[1]["version"] != v1
    nodes = {n["id"]: n for n in request(port, "GET", "/api/graph")[1]["nodes"]}
    assert nodes["b"]["effective_status"] == "ready"
    assert request(port, "DELETE", "/api/edges", {"from": "a", "to": "b"})[0] == 200
    assert request(port, "DELETE", "/api/nodes/a")[0] == 200
    assert set(Graph(dag_dir).nodes) == {"b"}


def test_rejects_foreign_host_origin_and_non_json(server):
    port, _ = server
    assert request(port, "GET", "/api/graph", headers={"Host": "evil.example:80"})[0] == 403
    status, _ = request(port, "POST", "/api/nodes", {"title": "x"}, headers={"Origin": "https://evil.example"})
    assert status == 403
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request("POST", "/api/nodes", body="title=x", headers={"Content-Type": "application/x-www-form-urlencoded"})
    res = conn.getresponse()
    assert res.status == 400 and b"application/json" in res.read()
    conn.close()


def test_rejects_unknown_fields(server):
    port, _ = server
    request(port, "POST", "/api/nodes", {"title": "A", "id": "a"})
    status, data = request(port, "PATCH", "/api/nodes/a", {"node_id": "x"})
    assert status == 400 and "cannot edit" in data["error"]


def test_patch_base_rev(server):
    port, dag_dir = server
    request(port, "POST", "/api/nodes", {"title": "A", "id": "a"})
    rev = {n["id"]: n["rev"] for n in request(port, "GET", "/api/graph")[1]["nodes"]}["a"]

    # matching revision: applied, and the response carries the new revision
    status, data = request(port, "PATCH", "/api/nodes/a", {"body": "mine", "base_rev": rev})
    assert status == 200 and data["node"]["body"].strip() == "mine" and data["node"]["rev"] != rev
    new_rev = data["node"]["rev"]

    # someone else edits the file; a save based on the old revision is refused
    Graph(dag_dir).update("a", status="done")
    status, data = request(port, "PATCH", "/api/nodes/a", {"body": "stale", "base_rev": new_rev})
    assert status == 409 and "changed on disk" in data["error"]
    assert data["node"]["status"] == "done" and data["node"]["body"].strip() == "mine"
    assert Graph(dag_dir).get("a").body.strip() == "mine"

    # retrying with the revision from the 409 goes through and keeps the other edit
    status, data = request(port, "PATCH", "/api/nodes/a", {"body": "mine again", "base_rev": data["node"]["rev"]})
    assert status == 200 and data["node"]["status"] == "done"

    # no base_rev: last writer wins, as for the CLI and MCP tools
    Graph(dag_dir).update("a", title="Renamed elsewhere")
    status, data = request(port, "PATCH", "/api/nodes/a", {"status": "todo"})
    assert status == 200 and data["node"]["status"] == "todo" and data["node"]["title"] == "Renamed elsewhere"
