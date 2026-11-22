import pytest

from claude_dag.graph import Graph
from claude_dag.model import DagError


@pytest.fixture
def g(tmp_path):
    return Graph.init(tmp_path)


def test_append_into_template_sections(g):
    g.add("A", id="a")
    g.append("a", "first result")
    g.append("a", "- second")
    g.append("a", "a note", section="Notes")
    body = g.nodes["a"].body
    assert "## Notes\na note\n\n## Result\nfirst result\n\n- second\n" in body
    assert Graph(g.dir).nodes["a"].body == body


def test_append_creates_missing_section(g):
    g.add("A", id="a", body="free text\n")
    g.append("a", "done it")
    assert g.nodes["a"].body == "free text\n\n## Result\ndone it\n"
    with pytest.raises(DagError, match="nothing to append"):
        g.append("a", "  \n")


def test_add_many_is_atomic_and_order_free(g):
    g.add_many([
        {"title": "Later", "id": "later", "deps": ["first"], "milestone": "ms"},
        {"title": "MS", "id": "ms", "kind": "milestone"},
        {"title": "First", "id": "first", "milestone": "ms"},
    ])
    assert g.statuses() == {"later": "todo", "ms": "todo", "first": "ready"}
    with pytest.raises(DagError, match="already exists"):
        g.add_many([{"title": "New", "id": "new"}, {"title": "Dup", "id": "first"}])
    with pytest.raises(DagError, match="unknown field"):
        g.add_many([{"title": "X", "owner": "me"}])
    assert set(Graph(g.dir).nodes) == {"later", "ms", "first"}


def test_add_many_generates_unique_ids(g):
    nodes = g.add_many([{"title": "Same"}, {"title": "Same"}])
    assert [n.id for n in nodes] == ["same", "same-2"]


def test_milestone_not_active_just_because_prereq_done(g):
    g.add_many([
        {"title": "M1", "id": "m1", "kind": "milestone"},
        {"title": "T1", "id": "t1", "milestone": "m1", "status": "done"},
        {"title": "M2", "id": "m2", "kind": "milestone", "deps": ["m1"]},
        {"title": "T2", "id": "t2", "milestone": "m2"},
    ])
    assert g.statuses()["m2"] == "todo"
    g.update("t2", status="active")
    assert g.statuses()["m2"] == "active"
