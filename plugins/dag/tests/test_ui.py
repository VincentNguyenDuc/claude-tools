"""Browser tests for the web UI (static/index.html), driven by Playwright.

They skip, rather than fail, when Playwright or its Chromium isn't installed.
Setup: `uv run --group dev playwright install --only-shell chromium`.
"""

import threading

import pytest

from claude_dag.graph import Graph
from claude_dag.server import make_server

sync_api = pytest.importorskip("playwright.sync_api")


@pytest.fixture(scope="module")
def browser():
    with sync_api.sync_playwright() as pw:
        try:
            b = pw.chromium.launch()
        except sync_api.Error as e:  # browser binary missing or unlaunchable
            pytest.skip(f"Chromium for Playwright not available: {str(e).splitlines()[0]}")
        yield b
        b.close()


@pytest.fixture
def dag(tmp_path):
    """A temp .claude-dag/ served on a free port. Yields (graph, base_url)."""
    graph = Graph.init(tmp_path)
    httpd = make_server(tmp_path / ".claude-dag", port=0)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield graph, f"http://127.0.0.1:{httpd.server_address[1]}/"
    httpd.shutdown()
    httpd.server_close()


@pytest.fixture
def page(browser):
    """A fresh page that records JS errors in page.js_errors."""
    ctx = browser.new_context()
    pg = ctx.new_page()
    pg.js_errors = []
    pg.on("pageerror", lambda exc: pg.js_errors.append(str(exc)))
    # HTTP error statuses (e.g. an expected 409) are logged as "Failed to load resource"; not JS errors.
    pg.on("console", lambda msg: msg.type == "error" and not msg.text.startswith("Failed to load resource")
          and pg.js_errors.append(msg.text))
    yield pg
    ctx.close()


def test_nodes_render_without_js_errors(dag, page):
    graph, url = dag
    graph.add_many([
        {"id": "m1", "title": "Milestone one", "kind": "milestone"},
        {"id": "a", "title": "First task", "milestone": "m1"},
        {"id": "b", "title": "Second task", "deps": ["a"], "milestone": "m1"},
    ])
    page.goto(url)
    page.wait_for_selector("#nodes .node[data-id='b']")
    ids = page.eval_on_selector_all("#nodes .node", "els => els.map(e => e.dataset.id)")
    assert set(ids) == {"m1", "a", "b"}
    assert "First task" in page.locator("#nodes .node[data-id='a']").text_content()
    assert page.locator("#edges > *").count() >= 1
    assert page.js_errors == []


def open_node(page, url, node_id):
    page.goto(url)
    page.click(f"#nodes .node[data-id='{node_id}']")
    page.wait_for_selector("#panel.open")


def test_save_sends_only_changed_fields(dag, page):
    graph, url = dag
    graph.add_many([{"id": "a", "title": "A"}])
    open_node(page, url, "a")
    page.fill("textarea[name=body]", "my notes")
    with page.expect_response(lambda r: r.request.method == "PATCH") as res:
        page.click("#form button[type=submit]")
    assert res.value.status == 200
    sent = res.value.request.post_data_json
    assert set(sent) == {"body", "base_rev"} and sent["body"] == "my notes"
    graph.reload()
    assert graph.get("a").body.strip() == "my notes"
    assert page.js_errors == []


def test_conflict_overwrite_keeps_other_edits(dag, page):
    graph, url = dag
    graph.add_many([{"id": "a", "title": "A"}])
    open_node(page, url, "a")
    page.fill("textarea[name=body]", "mine")
    graph.update("a", status="done")  # e.g. Claude finishes the node meanwhile
    page.click("#form button[type=submit]")
    page.wait_for_selector("#conflict.open")
    assert "Status" in page.inner_text("#conflict-list") and "done" in page.inner_text("#conflict-list")
    graph.reload()
    assert graph.get("a").body.strip() != "mine"  # nothing written before the user chooses
    page.click("#conflict-overwrite")
    page.wait_for_function("() => !document.querySelector('#conflict').classList.contains('open')")
    graph.reload()
    node = graph.get("a")
    assert node.body.strip() == "mine" and node.status == "done"
    assert page.input_value("select[name=status]") == "done"
    assert page.js_errors == []


def test_conflict_reload_discards_mine(dag, page):
    graph, url = dag
    graph.add_many([{"id": "a", "title": "A", "body": "original"}])
    open_node(page, url, "a")
    page.fill("textarea[name=body]", "mine")
    graph.update("a", body="theirs")
    page.click("#form button[type=submit]")
    page.wait_for_selector("#conflict.open")
    assert "Notes" in page.inner_text("#conflict-list")
    page.click("#conflict-reload")
    page.wait_for_function("() => !document.querySelector('#conflict').classList.contains('open')")
    assert page.input_value("textarea[name=body]").strip() == "theirs"
    graph.reload()
    assert graph.get("a").body.strip() == "theirs"
    assert page.js_errors == []


# ------------------------------------------------------------------ node dragging

def node_xy(page, node_id):
    """The node's layout position, parsed from its translate(x,y)."""
    t = page.get_attribute(f"#nodes .node[data-id='{node_id}']", "transform")
    x, y = t[len("translate("):-1].split(",")
    return float(x), float(y)


def edge_d(page, src, dst):
    return page.evaluate(
        """([src, dst]) => [...document.querySelectorAll('#edges .edge-hit')]
             .find(p => p.textContent === `${dst} depends on ${src}`).getAttribute('d')""",
        [src, dst],
    )


def drag_by(page, selector, dx, dy, shift=False):
    box = page.locator(selector).first.bounding_box()
    x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.mouse.move(x, y)
    if shift:
        page.keyboard.down("Shift")
    page.mouse.down()
    page.mouse.move(x + dx, y + dy, steps=6)
    page.mouse.up()
    if shift:
        page.keyboard.up("Shift")


def three_nodes(graph):
    graph.add_many([
        {"id": "a", "title": "A"},
        {"id": "b", "title": "B", "deps": ["a"]},
        {"id": "c", "title": "C", "deps": ["a", "b"]},  # a -> c skips a layer: routed via a waypoint
    ])


def test_drag_moves_pins_and_survives_reload(dag, page):
    from claude_dag.layout import read_layout

    graph, url = dag
    three_nodes(graph)
    page.goto(url)
    page.wait_for_selector("#nodes .node[data-id='c']")
    assert edge_d(page, "a", "c").count("C") == 2  # one waypoint
    bx, by = node_xy(page, "b")
    cx, cy = node_xy(page, "c")
    k = page.evaluate("() => view.k")

    with page.expect_response(lambda r: r.request.method == "PUT" and r.url.endswith("/api/layout")) as res:
        drag_by(page, "#nodes .node[data-id='c'] rect", 120, 90)
    assert res.value.status == 200
    saved = read_layout(graph.dir)
    assert set(saved) == {"c"}  # only the dragged node is pinned
    assert abs(saved["c"]["x"] - (cx + 120 / k)) < 2 and abs(saved["c"]["y"] - (cy + 90 / k)) < 2
    assert edge_d(page, "a", "c").count("C") == 1  # direct curve now
    assert not page.is_visible("#panel.open")  # a drag is not a click

    page.reload()
    page.wait_for_selector("#nodes .node[data-id='c']")
    assert node_xy(page, "c") == (saved["c"]["x"], saved["c"]["y"])
    assert node_xy(page, "b") == (bx, by)  # unpinned nodes still placed automatically
    assert page.js_errors == []


def test_drag_click_pan_and_shift_link_still_work(dag, page):
    graph, url = dag
    graph.add_many([{"id": "a", "title": "A"}, {"id": "b", "title": "B"}])
    page.goto(url)
    page.wait_for_selector("#nodes .node[data-id='b']")
    puts = []
    page.on("request", lambda r: r.method == "PUT" and puts.append(r.url))

    # a tiny wobble (under the threshold) is still a click
    drag_by(page, "#nodes .node[data-id='a'] rect", 1, 1)
    page.wait_for_selector("#panel.open")
    assert page.input_value("input[name=id]") == "a"
    page.click("#close")

    # dragging empty canvas pans the view, nodes keep their layout position
    before_view = page.get_attribute("#viewport", "transform")
    before_a = node_xy(page, "a")
    svg = page.locator("#canvas").bounding_box()
    page.mouse.move(svg["x"] + svg["width"] - 20, svg["y"] + svg["height"] - 60)
    page.mouse.down()
    page.mouse.move(svg["x"] + svg["width"] - 120, svg["y"] + svg["height"] - 100, steps=5)
    page.mouse.up()
    assert page.get_attribute("#viewport", "transform") != before_view
    assert node_xy(page, "a") == before_a

    # shift+drag from a onto b adds a dependency instead of moving a
    box_b = page.locator("#nodes .node[data-id='b'] rect").bounding_box()
    box_a = page.locator("#nodes .node[data-id='a'] rect").bounding_box()
    with page.expect_response(lambda r: r.url.endswith("/api/edges")):
        drag_by(page, "#nodes .node[data-id='a'] rect",
                box_b["x"] - box_a["x"], box_b["y"] - box_a["y"], shift=True)
    graph.reload()
    assert graph.get("b").deps == ["a"]
    assert puts == []  # neither the click, the pan nor the link saved a layout
    assert page.js_errors == []


def test_drag_unpin_and_reset_layout(dag, page):
    import json

    from claude_dag.layout import LAYOUT_FILE, read_layout

    graph, url = dag
    three_nodes(graph)
    page.goto(url)
    page.wait_for_selector("#nodes .node[data-id='c']")
    auto = {i: node_xy(page, i) for i in "abc"}
    (graph.dir / LAYOUT_FILE).write_text(json.dumps({"positions": {
        "a": {"x": 900, "y": 500}, "c": {"x": -300, "y": 400}}}))
    page.reload()
    page.wait_for_selector("#nodes .node[data-id='c']")
    assert node_xy(page, "a") == (900, 500) and node_xy(page, "c") == (-300, 400)

    # Unpin in the panel: only that node goes back to its automatic place
    page.click("#nodes .node[data-id='a']")
    page.wait_for_selector("#unpin", state="visible")
    with page.expect_response(lambda r: r.request.method == "PUT"):
        page.click("#unpin")
    page.wait_for_selector("#unpin", state="hidden")
    assert set(read_layout(graph.dir)) == {"c"}
    assert node_xy(page, "a") == auto["a"]
    page.click("#close")

    # Reset layout asks first; dismissing keeps everything
    page.once("dialog", lambda d: d.dismiss())
    page.click("#reset-layout")
    assert set(read_layout(graph.dir)) == {"c"}
    page.once("dialog", lambda d: d.accept())
    with page.expect_response(lambda r: r.request.method == "PUT"):
        page.click("#reset-layout")
    assert read_layout(graph.dir) == {}
    page.wait_for_function("() => !Object.keys(positions).length")
    assert node_xy(page, "c") == auto["c"]
    assert page.js_errors == []
