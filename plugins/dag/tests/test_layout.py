import json

from test_server import request, server  # noqa: F401  (server is a fixture)

from claude_dag.graph import Graph, dir_version
from claude_dag.layout import LAYOUT_FILE, layout_version, read_layout


def setup_nodes(dag_dir):
    graph = Graph(dag_dir)
    graph.add_many([{"id": "a", "title": "A"}, {"id": "b", "title": "B", "deps": ["a"]}])
    return graph


def test_round_trip_merge_and_replace(server):
    port, dag_dir = server
    setup_nodes(dag_dir)
    assert request(port, "GET", "/api/layout")[1] == {"positions": {}, "version": "0"}
    nodes_version = dir_version(dag_dir)

    status, data = request(port, "PUT", "/api/layout", {"positions": {"a": {"x": 10, "y": 20.25}}})
    assert status == 200 and data["positions"] == {"a": {"x": 10.0, "y": 20.2}}
    status, data = request(port, "PUT", "/api/layout", {"positions": {"b": {"x": 1, "y": 2}}})
    assert set(data["positions"]) == {"a", "b"}  # merged
    status, data = request(port, "GET", "/api/layout")
    assert data["positions"]["b"] == {"x": 1.0, "y": 2.0} and data["version"] != "0"

    # null removes one id; replace drops everything not given
    data = request(port, "PUT", "/api/layout", {"positions": {"a": None}})[1]
    assert set(data["positions"]) == {"b"}
    data = request(port, "PUT", "/api/layout", {"positions": {"a": {"x": 5, "y": 5}}, "replace": True})[1]
    assert data["positions"] == {"a": {"x": 5.0, "y": 5.0}}

    # layout changes don't touch the node files' version, and have their own
    assert dir_version(dag_dir) == nodes_version
    versions = request(port, "GET", "/api/version")[1]
    assert versions["version"] == nodes_version and versions["layout"] == layout_version(dag_dir)
    assert not list(dag_dir.glob(".layout.json.*"))  # no temp files left behind


def test_put_validation_and_unknown_ids(server):
    port, dag_dir = server
    setup_nodes(dag_dir)
    data = request(port, "PUT", "/api/layout", {"positions": {"a": {"x": 1, "y": 1}, "ghost": {"x": 0, "y": 0}}})[1]
    assert set(data["positions"]) == {"a"}
    for bad in ({"a": {"x": "nope", "y": 1}}, {"a": [1, 2]}, ["a"]):
        status, data = request(port, "PUT", "/api/layout", {"positions": bad})
        assert status == 400, bad
    assert request(port, "PUT", "/api/layout", {"pos": {}})[0] == 400


def test_unknown_ids_dropped_on_read(server):
    port, dag_dir = server
    setup_nodes(dag_dir)
    (dag_dir / LAYOUT_FILE).write_text(json.dumps({"positions": {"a": {"x": 1, "y": 2}, "gone": {"x": 3, "y": 4}}}))
    assert request(port, "GET", "/api/layout")[1]["positions"] == {"a": {"x": 1.0, "y": 2.0}}


def test_rename_and_remove_follow_layout(tmp_path):
    graph = Graph.init(tmp_path)
    setup_nodes(graph.dir)
    (graph.dir / LAYOUT_FILE).write_text(json.dumps({"positions": {"a": {"x": 1, "y": 2}, "b": {"x": 3, "y": 4}}}))
    graph = Graph(graph.dir)
    graph.update("a", id="first")
    assert read_layout(graph.dir) == {"first": {"x": 1.0, "y": 2.0}, "b": {"x": 3.0, "y": 4.0}}
    graph.remove("b")
    assert read_layout(graph.dir) == {"first": {"x": 1.0, "y": 2.0}}
    graph.remove("first")
    assert read_layout(graph.dir) == {}


def test_corrupt_or_missing_file(server):
    port, dag_dir = server
    graph = setup_nodes(dag_dir)
    for junk in ("{not json", "[]", '{"positions": 3}', "\xff"):
        (dag_dir / LAYOUT_FILE).write_text(junk, encoding="latin-1")
        status, data = request(port, "GET", "/api/layout")
        assert status == 200 and data["positions"] == {}, junk
        assert request(port, "GET", "/api/graph")[0] == 200
        graph.update("a", title="A again")  # rename/remove hooks don't trip on it either
    graph.update("a", id="a2")
    graph.remove("a2", force=True)
    # a PUT replaces the corrupt file with a valid one
    status, data = request(port, "PUT", "/api/layout", {"positions": {"b": {"x": 0, "y": 0}}})
    assert status == 200 and read_layout(dag_dir) == {"b": {"x": 0.0, "y": 0.0}}
    (dag_dir / LAYOUT_FILE).unlink()
    assert request(port, "GET", "/api/layout")[1] == {"positions": {}, "version": "0"}


def test_put_checks_origin_and_json(server):
    port, dag_dir = server
    setup_nodes(dag_dir)
    body = {"positions": {"a": {"x": 1, "y": 1}}}
    assert request(port, "PUT", "/api/layout", body, headers={"Origin": "https://evil.example"})[0] == 403
    assert request(port, "PUT", "/api/layout", body, headers={"Host": "evil.example"})[0] == 403
    status, _ = request(port, "PUT", "/api/layout", body, headers={"Content-Type": "text/plain"})
    assert status == 400
    assert not (dag_dir / LAYOUT_FILE).exists()
