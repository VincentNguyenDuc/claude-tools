import pytest

from claude_dag.graph import Graph, find_dag_dir
from claude_dag.model import DEFAULT_BODY, DagError, Node


@pytest.fixture
def g(tmp_path):
    return Graph.init(tmp_path)


def test_markdown_roundtrip():
    node = Node(
        id="a", title="A: thing", kind="research", status="active", deps=["b", "c"],
        milestone="m", verify="pytest -q", body="## Notes\nhello\n", extra={"owner": "me"},
    )
    text = node.to_markdown()
    assert "deps: [b, c]" in text
    assert Node.from_markdown(text, "a") == node


def test_parse_lenient_fields():
    text = "---\ntitle: X\nstatus: ready\ndeps: a, b\n---\nbody\n"
    node = Node.from_markdown(text, "x")
    assert (node.id, node.status, node.deps, node.body) == ("x", "todo", ["a", "b"], "body\n")


def test_no_frontmatter_is_all_body():
    node = Node.from_markdown("just notes\n", "n")
    assert node.title == "n" and node.body == "just notes\n"


def test_add_writes_file_and_log(g):
    node = g.add("Design the schema")
    assert node.id == "design-the-schema"
    assert g.path_for(node.id).read_text().startswith("---\nid: design-the-schema\n")
    assert node.body == DEFAULT_BODY
    assert "added `design-the-schema`" in (g.dir / "log.md").read_text()
    assert g.add("Design the schema").id == "design-the-schema-2"


def test_ready_and_milestone_status(g):
    g.add("M1", id="m1", kind="milestone")
    g.add("Schema", id="schema", milestone="m1")
    g.add("Core", id="core", deps=["schema"], milestone="m1")
    st = g.statuses()
    assert (st["schema"], st["core"], st["m1"]) == ("ready", "todo", "todo")
    g.update("schema", status="done")
    st = g.statuses()
    assert (st["core"], st["m1"]) == ("ready", "active")
    g.update("core", status="failed")
    assert g.statuses()["m1"] == "failed"
    g.update("core", status="done")
    assert g.statuses()["m1"] == "done"
    assert [n.id for n in g.ready()] == []


def test_dropped_dep_satisfies(g):
    g.add("A", id="a")
    g.add("B", id="b", deps=["a"])
    g.update("a", status="dropped")
    assert g.statuses()["b"] == "ready"


def test_link_cycle_rejected_and_not_written(g):
    g.add("A", id="a")
    g.add("B", id="b", deps=["a"])
    with pytest.raises(DagError, match="cycle"):
        g.link("b", "a")
    assert Graph(g.dir).nodes["a"].deps == []


def test_cycle_through_milestone_membership(g):
    g.add("M", id="m", kind="milestone")
    with pytest.raises(DagError, match="cycle"):
        g.add("T", id="t", deps=["m"], milestone="m")
    assert "t" not in Graph(g.dir).nodes


def test_unknown_refs_rejected(g):
    with pytest.raises(DagError, match="unknown deps"):
        g.add("X", deps=["nope"])
    g.add("Task", id="task")
    with pytest.raises(DagError, match="not a milestone"):
        g.add("Y", milestone="task")


def test_rename_updates_references(g):
    g.add("M", id="m", kind="milestone")
    g.add("A", id="a", milestone="m")
    g.add("B", id="b", deps=["a"])
    g.update("a", id="alpha")
    fresh = Graph(g.dir)
    assert set(fresh.nodes) == {"m", "alpha", "b"}
    assert fresh.nodes["b"].deps == ["alpha"]
    assert fresh.members("m") == ["alpha"]
    assert not g.path_for("a").exists()


def test_remove_requires_force(g):
    g.add("A", id="a")
    g.add("B", id="b", deps=["a"])
    with pytest.raises(DagError, match="referenced by: b"):
        g.remove("a")
    g.remove("a", force=True)
    fresh = Graph(g.dir)
    assert set(fresh.nodes) == {"b"} and fresh.nodes["b"].deps == []


def test_hand_edited_files_validate(g):
    (g.nodes_dir / "x.md").write_text("---\nid: y\ntitle: X\ndeps: [ghost]\nkind: wat\n---\n")
    (g.nodes_dir / "bad.md").write_text("---\ntitle: [unclosed\n---\n")
    fresh = Graph(g.dir)
    errors = "\n".join(fresh.validate())
    assert "does not match file name" in errors
    assert "missing node 'ghost'" in errors
    assert "unknown kind 'wat'" in errors
    assert "bad.md: bad frontmatter" in errors
    assert fresh.statuses()["x"] == "todo"  # dangling dep is never satisfied


def test_existing_cycle_does_not_block_fixes(g):
    g.add("A", id="a")
    g.add("B", id="b", deps=["a"])
    (g.nodes_dir / "a.md").write_text("---\nid: a\ntitle: A\ndeps: [b]\n---\n")
    fresh = Graph(fresh_dir := g.dir)
    assert fresh.find_cycle()
    fresh.unlink("b", "a")
    assert Graph(fresh_dir).find_cycle() is None


def test_verify_marks_done_or_failed(g):
    g.add("Ok", id="ok", verify="echo hi")
    g.add("Bad", id="bad", verify="echo boom >&2; exit 3")
    assert g.verify("ok") == (True, "hi\n")
    ok, out = g.verify("bad")
    assert not ok and "boom" in out
    assert (g.nodes["ok"].status, g.nodes["bad"].status) == ("done", "failed")
    log = (g.dir / "log.md").read_text()
    assert "verify `bad`: FAIL (exit 3)" in log


def test_find_dag_dir_walks_up(g, tmp_path):
    sub = tmp_path / "a" / "b"
    sub.mkdir(parents=True)
    assert find_dag_dir(sub) == g.dir.resolve()


def test_summary(g):
    g.add("M", id="m", kind="milestone")
    g.add("A", id="a", milestone="m", status="done")
    g.add("B", id="b", milestone="m", deps=["a"])
    text = g.summary()
    assert "◆ m — M [1/2] active" in text
    assert "Ready:\n  - b: B" in text
