import json
import os
import sys

import anyio
import pytest
from mcp import Client, StdioServerParameters

from claude_dag.graph import Graph
from claude_dag.mcp_server import server


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    Graph.init(tmp_path)
    return tmp_path


def call(target, name, args=None):
    async def go():
        async with Client(target) as client:
            return await client.call_tool(name, args or {})

    return anyio.run(go)


def payload(result):
    # Lists and strings are wrapped as {"result": ...}; dicts are sent as-is.
    content = result.structured_content
    return content["result"] if set(content) == {"result"} else content


def test_tools_listed():
    async def go():
        async with Client(server) as client:
            return [t.name for t in (await client.list_tools()).tools]

    names = anyio.run(go)
    assert {"dag_summary", "dag_add_many", "dag_ready", "dag_verify", "dag_append"} <= set(names)


def test_plan_work_verify_loop(project):
    nodes = [
        {"title": "Ship", "id": "ship", "kind": "milestone"},
        {"title": "Build", "id": "build", "deps": ["design"], "milestone": "ship", "verify": "echo built"},
        {"title": "Design", "id": "design", "kind": "decision", "milestone": "ship"},
    ]
    assert not call(server, "dag_add_many", {"nodes": nodes}).is_error
    ready = payload(call(server, "dag_ready"))
    assert [n["id"] for n in ready] == ["design"] and "## Goal / acceptance" in ready[0]["body"]

    call(server, "dag_update", {"id": "design", "status": "active"})
    call(server, "dag_append", {"id": "design", "text": "Chose X because Y."})
    call(server, "dag_update", {"id": "design", "status": "done"})
    result = payload(call(server, "dag_verify", {"id": "build"}))
    assert result["passed"] and result["output_tail"] == "built"

    summary = payload(call(server, "dag_summary"))
    assert "◆ ship — Ship [2/2] done" in summary
    body = Graph(project / ".claude-dag").nodes["design"].body
    assert "## Result\nChose X because Y.\n" in body


def test_errors_are_readable(project):
    call(server, "dag_add_many", {"nodes": [{"title": "A", "id": "a"}, {"title": "B", "id": "b", "deps": ["a"]}]})
    result = call(server, "dag_link", {"src": "b", "dst": "a"})
    assert result.is_error and "cycle" in result.content[0].text
    result = call(server, "dag_add_many", {"nodes": [{"title": "C", "deps": ["ghost"]}]})
    assert result.is_error and "unknown deps: ghost" in result.content[0].text
    assert set(Graph(project / ".claude-dag").nodes) == {"a", "b"}


def test_no_dag_dir_tells_how_to_init(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    result = call(server, "dag_summary")
    assert result.is_error and "dag_init" not in result.content[0].text  # CLI hint is fine
    assert not call(server, "dag_init").is_error
    assert (tmp_path / ".claude-dag" / "nodes").is_dir()


def test_stdio_subprocess(project):
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "claude_dag.mcp_server"],
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(project)},
    )
    result = call(params, "dag_add", {"title": "Hello", "deps": []})
    assert not result.is_error
    assert json.loads(result.content[0].text)["id"] == "hello"
    assert (project / ".claude-dag" / "nodes" / "hello.md").exists()
