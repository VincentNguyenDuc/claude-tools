import json

from claude_dag.cli import main


def run(tmp_path, capsys, *args):
    code = main(["--dir", str(tmp_path), *args])
    out = capsys.readouterr()
    return code, out.out, out.err


def test_flow(tmp_path, capsys):
    assert run(tmp_path, capsys, "init", str(tmp_path))[0] == 0
    assert run(tmp_path, capsys, "add", "Milestone one", "--id", "m1", "-k", "milestone")[0] == 0
    assert run(tmp_path, capsys, "add", "Schema", "-m", "m1")[0] == 0
    assert run(tmp_path, capsys, "add", "Core", "-d", "schema", "-m", "m1", "-v", "true")[0] == 0

    _, out, _ = run(tmp_path, capsys, "ready")
    assert out.strip() == "▶ schema: Schema"

    assert run(tmp_path, capsys, "done", "schema")[0] == 0
    _, out, _ = run(tmp_path, capsys, "ready", "--json")
    assert [n["id"] for n in json.loads(out)] == ["core"]

    code, out, _ = run(tmp_path, capsys, "verify", "core")
    assert code == 0 and "PASS: core -> done" in out

    _, out, _ = run(tmp_path, capsys, "list")
    lines = out.splitlines()
    assert lines[0].startswith("✓ done") and "schema" in lines[0]
    assert "◆ Milestone one" in lines[-1]

    assert run(tmp_path, capsys, "validate")[1].strip() == "ok"


def test_errors_exit_2(tmp_path, capsys):
    run(tmp_path, capsys, "init", str(tmp_path))
    run(tmp_path, capsys, "add", "A", "--id", "a")
    run(tmp_path, capsys, "add", "B", "--id", "b", "-d", "a")
    code, _, err = run(tmp_path, capsys, "link", "b", "a")
    assert code == 2 and "cycle" in err
    code, _, err = run(tmp_path, capsys, "edit", "a")
    assert code == 2 and "nothing to change" in err


def test_edit_deps_and_rename(tmp_path, capsys):
    run(tmp_path, capsys, "init", str(tmp_path))
    for node_id in ("a", "b", "c"):
        run(tmp_path, capsys, "add", node_id.upper(), "--id", node_id)
    assert run(tmp_path, capsys, "edit", "c", "--add-dep", "a", "--add-dep", "b")[0] == 0
    assert run(tmp_path, capsys, "edit", "c", "--rm-dep", "a", "--rename", "gamma")[0] == 0
    _, out, _ = run(tmp_path, capsys, "show", "gamma", "--json")
    assert json.loads(out)["deps"] == ["b"]


def test_no_dag_dir(tmp_path, capsys):
    code, _, err = run(tmp_path, capsys, "list")
    assert code == 2 and "claude-dag init" in err


def test_import_and_append(tmp_path, capsys):
    run(tmp_path, capsys, "init", str(tmp_path))
    plan = tmp_path / "plan.yaml"
    plan.write_text("- {title: Later, id: later, deps: [first]}\n- {title: First, id: first}\n")
    code, out, _ = run(tmp_path, capsys, "import", str(plan))
    assert code == 0 and "added 2 nodes: later, first" in out
    assert run(tmp_path, capsys, "append", "first", "it worked")[0] == 0
    _, out, _ = run(tmp_path, capsys, "show", "first", "--json")
    assert json.loads(out)["body"].endswith("## Result\nit worked\n")
