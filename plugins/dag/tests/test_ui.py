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
    ctx = browser.new_context(viewport={"width": 1600, "height": 900})  # room for the graph + panel
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


def edit_body(page, text):
    """Switch the notes from the rendered preview to the editor and type into it."""
    if not page.is_visible("textarea[name=body]"):
        page.click("#body-toggle")
    page.fill("textarea[name=body]", text)


def test_save_sends_only_changed_fields(dag, page):
    graph, url = dag
    graph.add_many([{"id": "a", "title": "A"}])
    open_node(page, url, "a")
    edit_body(page, "my notes")
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
    edit_body(page, "mine")
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
    edit_body(page, "mine")
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


# ------------------------------------------------------------------ notes preview

PREVIEW_BODY = """## Goal / acceptance

- First **bold** point with `inline code`
- [x] done item
- [ ] open item
  - nested *point*
1. one
2. two

See [the docs](https://example.com/docs) or https://example.org/x.

```sh
uv run pytest -q
```
"""


def test_preview_renders_markdown(dag, page):
    graph, url = dag
    graph.add_many([{"id": "a", "title": "A", "body": PREVIEW_BODY}])
    open_node(page, url, "a")
    pv = page.locator("#preview")
    assert pv.is_visible() and not page.is_visible("textarea[name=body]")
    assert pv.locator("h2").inner_text() == "Goal / acceptance"
    assert pv.locator(":scope > ul > li").count() == 3 and pv.locator("ul ul > li").inner_text() == "nested point"
    assert pv.locator("ol > li").count() == 2
    assert pv.locator("strong").inner_text() == "bold" and pv.locator("em").inner_text() == "point"
    boxes = pv.locator("li.task input[type=checkbox]")
    assert boxes.count() == 2 and boxes.nth(0).is_checked() and not boxes.nth(1).is_checked()
    assert pv.locator("li code").inner_text() == "inline code"
    assert pv.locator("pre code").inner_text().strip() == "uv run pytest -q"
    links = pv.locator("a")
    assert links.count() == 2
    for i, href in enumerate(["https://example.com/docs", "https://example.org/x"]):
        assert links.nth(i).get_attribute("href") == href
        assert links.nth(i).get_attribute("target") == "_blank"
        assert "noopener" in links.nth(i).get_attribute("rel")

    # Edit toggles to the textarea; Preview renders what was typed
    edit_body(page, "# New heading\n\ntext")
    page.click("#body-toggle")
    assert pv.locator("h1").inner_text() == "New heading"
    assert page.js_errors == []


def test_preview_escapes_html_and_unsafe_links(dag, page):
    graph, url = dag
    evil = "\n".join([
        "<script>window.__pwned = 'script'</script>",
        '<img src=x onerror="window.__pwned = \'img\'">',
        "## <b onmouseover=\"window.__pwned='h'\">head</b>",
        "- [click](javascript:window.__pwned='js')",
        "- [data](data:text/html,<script>alert(1)</script>)",
        "`<svg onload=\"window.__pwned='code'\">`",
    ])
    graph.add_many([{"id": "a", "title": "A", "body": evil}])
    open_node(page, url, "a")
    pv = page.locator("#preview")
    page.wait_for_timeout(200)  # give any injected handler a chance to fire
    assert pv.locator("script, img, svg, b, iframe").count() == 0
    assert pv.locator("a").count() == 0  # javascript: and data: links stay plain text
    text = pv.inner_text()
    assert "<script>" in text and "onerror=" in text and "javascript:" in text
    pv.locator("li", has_text="click").click()
    pv.hover()
    assert page.evaluate("() => window.__pwned") is None
    assert page.js_errors == []


# ------------------------------------------------------------------ trace highlight

def lit_nodes(page):
    if not page.evaluate("() => document.querySelector('#canvas').classList.contains('trace')"):
        return None
    return set(page.eval_on_selector_all("#nodes .node.lit", "els => els.map(e => e.dataset.id)"))


def lit_edges(page):
    return set(page.eval_on_selector_all(
        "#edges .edge.lit", "els => els.map(e => e.dataset.from + '>' + e.dataset.to)"))


def trace_graph(graph):
    graph.add_many([
        {"id": "a", "title": "A"},
        {"id": "b", "title": "B", "deps": ["a"]},
        {"id": "c", "title": "C", "deps": ["b"]},
        {"id": "d", "title": "D", "deps": ["a"]},  # sibling branch: not on b's chain
        {"id": "e", "title": "E"},                 # unrelated
    ])


def test_trace_on_hover_and_selection(dag, page):
    graph, url = dag
    trace_graph(graph)
    page.goto(url)
    page.wait_for_selector("#nodes .node[data-id='e']")
    assert lit_nodes(page) is None

    page.hover("#nodes .node[data-id='b'] rect")
    assert lit_nodes(page) == {"a", "b", "c"}
    assert lit_edges(page) == {"a>b", "b>c"}  # a>d stays dim
    page.hover("#nodes .node[data-id='a'] rect")
    assert lit_nodes(page) == {"a", "b", "c", "d"}

    page.mouse.move(2, 2)  # off any node: highlight clears
    assert lit_nodes(page) is None

    page.click("#nodes .node[data-id='d'] rect")  # selecting keeps it lit after mouse-out
    page.wait_for_selector("#panel.open")
    page.mouse.move(2, 2)
    assert lit_nodes(page) == {"a", "d"}
    page.hover("#nodes .node[data-id='c'] rect")  # hover wins while hovering
    assert lit_nodes(page) == {"a", "b", "c"}
    page.mouse.move(2, 2)
    assert lit_nodes(page) == {"a", "d"}
    page.click("#close")
    assert lit_nodes(page) is None
    assert page.js_errors == []


def test_trace_with_filters(dag, page):
    graph, url = dag
    trace_graph(graph)
    graph.add_many([{"id": "m", "title": "M", "kind": "milestone"}])
    graph.update("b", milestone="m")
    graph.update("c", milestone="m")
    graph.update("b", status="done")
    page.goto(url)
    page.wait_for_selector("#nodes .node[data-id='m']")

    # hide done: b disappears, but a and c are still connected through it
    page.check("#hide-done")
    page.wait_for_selector("#nodes .node[data-id='b']", state="detached")
    page.hover("#nodes .node[data-id='c'] rect")
    assert lit_nodes(page) == {"a", "c", "m"}
    page.mouse.move(2, 2)
    page.uncheck("#hide-done")

    # milestone filter: only m and its members are drawn
    page.select_option("#filter-ms", "m")
    page.wait_for_selector("#nodes .node[data-id='a']", state="detached")
    page.hover("#nodes .node[data-id='b'] rect")
    assert lit_nodes(page) == {"b", "c", "m"}
    assert "b>c" in lit_edges(page)
    assert page.js_errors == []


# ------------------------------------------------------------------ search

def search_graph(graph):
    graph.add_many([
        {"id": "m", "title": "Milestone", "kind": "milestone"},
        {"id": "parser", "title": "Write the parser", "milestone": "m"},
        {"id": "cfg", "title": "Parse config", "deps": ["parser"], "milestone": "m"},
        {"id": "deploy-prod", "title": "Ship it", "deps": ["cfg"], "status": "done"},
        *({"id": f"filler-{i}", "title": f"Filler {i}"} for i in range(12)),
    ])


def results(page):
    return page.eval_on_selector_all("#search-results li[data-id]", "els => els.map(e => e.dataset.id)")


def assert_centred(page, node_id):
    node = page.locator(f"#nodes .node[data-id='{node_id}'] rect").bounding_box()
    stage = page.locator("#canvas").bounding_box()
    cx, cy = node["x"] + node["width"] / 2, node["y"] + node["height"] / 2
    assert abs(cx - (stage["x"] + stage["width"] / 2)) < 3
    assert abs(cy - (stage["y"] + stage["height"] / 2)) < 3


def test_search_matches_selects_and_centres(dag, page):
    graph, url = dag
    search_graph(graph)
    page.goto(url)
    page.wait_for_selector("#nodes .node[data-id='cfg']")

    page.keyboard.press("/")
    page.wait_for_selector("#search.open")
    page.keyboard.type("PARS")  # case-insensitive, matches ids and titles
    assert set(results(page)) == {"parser", "cfg"}
    assert results(page)[0] == "parser"  # id prefix ranks first
    page.fill("#search-input", "zzz")
    assert results(page) == [] and "No match" in page.inner_text("#search-results")

    page.fill("#search-input", "config")
    page.keyboard.press("Enter")
    page.wait_for_selector("#panel.open")
    assert not page.is_visible("#search")
    assert page.input_value("input[name=id]") == "cfg"
    assert "selected" in page.get_attribute("#nodes .node[data-id='cfg']", "class")
    assert_centred(page, "cfg")

    # Cmd/Ctrl+K opens it too; arrows pick; Esc closes the box but not the panel
    page.keyboard.press("ControlOrMeta+k")
    page.wait_for_selector("#search.open")
    page.keyboard.type("filler-1")  # filler-1, filler-10, filler-11
    page.keyboard.press("ArrowDown")
    assert page.get_attribute("#search-results li.active", "data-id") == results(page)[1]
    page.keyboard.press("Escape")
    assert not page.is_visible("#search") and page.is_visible("#panel.open")
    assert page.input_value("input[name=id]") == "cfg"
    assert page.js_errors == []


def test_search_clears_hiding_filter(dag, page):
    graph, url = dag
    search_graph(graph)
    page.goto(url)
    page.wait_for_selector("#nodes .node[data-id='cfg']")

    page.check("#hide-done")
    page.wait_for_selector("#nodes .node[data-id='deploy-prod']", state="detached")
    page.keyboard.press("/")
    page.keyboard.type("ship")
    page.keyboard.press("Enter")
    page.wait_for_selector("#nodes .node[data-id='deploy-prod']")
    assert not page.is_checked("#hide-done")
    assert page.input_value("input[name=id]") == "deploy-prod"
    assert_centred(page, "deploy-prod")
    page.click("#close")

    # milestone filter: a node outside it clears the filter; a node inside keeps it
    page.select_option("#filter-ms", "m")
    page.wait_for_selector("#nodes .node[data-id='filler-3']", state="detached")
    page.keyboard.press("/")
    page.keyboard.type("parser")
    page.keyboard.press("Enter")
    assert page.input_value("#filter-ms") == "m"
    page.click("#close")
    page.keyboard.press("/")
    page.keyboard.type("filler 3")
    page.keyboard.press("Enter")
    page.wait_for_selector("#nodes .node[data-id='filler-3']")
    assert page.input_value("#filter-ms") == ""
    assert_centred(page, "filler-3")
    assert page.js_errors == []


# ------------------------------------------------------------------ labels

LONG_TITLE = ("Investigate why the nightly integration pipeline sometimes times out on the "
              "artifact upload step and propose a fix")
ID30 = "aaaaaaaaaa-decision-thirty-chx"  # 30 characters


def node_info(page, node_id):
    return page.evaluate(
        """id => {
          const g = document.querySelector(`#nodes .node[data-id="${id}"]`), r = g.querySelector('rect');
          return {
            w: +r.getAttribute('width'), h: +r.getAttribute('height'),
            lines: [...g.querySelectorAll('text.title')].map(t => [t.textContent, t.getComputedTextLength()]),
            sub: [g.querySelector('text.sub').textContent, g.querySelector('text.sub').getComputedTextLength()],
            tip: g.querySelector('title').textContent,
            box: g.getBBox ? (({x, y, width, height}) => ({x, y, width, height}))(r.getBBox()) : null,
            pos: g.getAttribute('transform'),
          };
        }""",
        node_id,
    )


def test_labels_wrap_and_keep_id_line(dag, page):
    graph, url = dag
    assert len(ID30) == 30
    graph.add_many([
        {"id": "short", "title": "Short"},
        {"id": "two", "title": "Wrap this title onto exactly two lines please"},
        {"id": "long", "title": LONG_TITLE},
        # long ids in later columns, so column 0 keeps the minimum width
        {"id": ID30, "title": "Long id", "kind": "decision", "status": "blocked", "deps": ["short"]},
        {"id": "m" * 30, "title": "Milestone", "kind": "milestone", "deps": [ID30]},
    ])
    page.goto(url)
    page.wait_for_selector(f"#nodes .node[data-id='{'m' * 30}']")

    short, two, long_ = (node_info(page, i) for i in ("short", "two", "long"))
    assert [t for t, _ in short["lines"]] == ["Short"] and short["h"] == 52
    assert len(two["lines"]) == 2 and two["h"] == 68
    assert " ".join(t for t, _ in two["lines"]) == "Wrap this title onto exactly two lines please"
    assert len(long_["lines"]) == 2 and long_["lines"][1][0].endswith("…")
    assert not long_["lines"][0][0].endswith("…")
    assert long_["tip"].startswith(LONG_TITLE)  # full title on hover
    assert short["w"] == two["w"] == long_["w"] == 210
    assert node_info(page, ID30)["w"] > 210  # only the long-id column widens
    for info in (short, two, long_):
        for _, width in info["lines"]:
            assert width <= info["w"] - 20 + 1

    # id/status line: never cut for 30-char ids, even with kind and milestone counts
    for node_id, expect in [(ID30, f"blocked · decision · {ID30}"), ("m" * 30, None)]:
        info = node_info(page, node_id)
        text, width = info["sub"]
        assert "…" not in text and node_id in text
        if expect:
            assert text == expect
        assert width <= info["w"] - 20 + 1

    # layout spacing accounts for heights: no two nodes overlap
    boxes = page.eval_on_selector_all(
        "#nodes .node", """els => els.map(g => { const r = g.querySelector('rect').getBoundingClientRect();
                                         return [r.left, r.top, r.right, r.bottom]; })""")
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            assert a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1], (a, b)
    assert page.js_errors == []


def screen_box(page, selector):
    b = page.locator(selector).first.bounding_box()
    return b["x"], b["y"], b["x"] + b["width"], b["y"] + b["height"]


def contains(outer, inner):
    return outer[0] <= inner[0] and outer[1] <= inner[1] and outer[2] >= inner[2] and outer[3] >= inner[3]


def test_groups_box_members_follow_drag_and_toggle(dag, page):
    graph, url = dag
    graph.add_many([
        {"id": "m1", "title": "First milestone", "kind": "milestone"},
        {"id": "m2", "title": "Second milestone", "kind": "milestone", "deps": ["m1"]},
        {"id": "m3", "title": "Empty milestone", "kind": "milestone"},
        {"id": "a", "title": "A", "milestone": "m1"},
        {"id": "b", "title": "B", "deps": ["a"], "milestone": "m1"},
        {"id": "c", "title": "C", "deps": ["b"], "milestone": "m2"},
        {"id": "loose", "title": "Loose"},
    ])
    page.goto(url)
    page.wait_for_selector("#groups .group[data-id='m2']")
    assert set(page.eval_on_selector_all("#groups .group", "els => els.map(e => e.dataset.id)")) == {"m1", "m2"}
    assert "First milestone" in page.text_content("#groups .group[data-id='m1'] text")
    # behind nodes and edges, and never catches the mouse
    assert page.evaluate("() => [...document.querySelector('#viewport').children].map(e => e.id)")[:2] == ["groups", "edges"]
    assert page.evaluate("() => getComputedStyle(document.querySelector('.group')).pointerEvents") == "none"
    hues = page.eval_on_selector_all("#groups .group", "els => els.map(e => e.style.getPropertyValue('--h'))")
    assert len(set(hues)) == 2

    g1 = screen_box(page, "#groups .group[data-id='m1'] rect")
    for n in ("a", "b"):
        assert contains(g1, screen_box(page, f"#nodes .node[data-id='{n}'] rect"))
    assert not contains(g1, screen_box(page, "#nodes .node[data-id='c'] rect"))

    # dragging a member stretches its box, live and after the drop
    drag_by(page, "#nodes .node[data-id='b'] rect", 0, 260)
    g1 = screen_box(page, "#groups .group[data-id='m1'] rect")
    assert contains(g1, screen_box(page, "#nodes .node[data-id='b'] rect"))
    assert contains(g1, screen_box(page, "#nodes .node[data-id='a'] rect"))

    # hidden members don't count; a box with no visible members disappears
    graph.update("c", status="done")
    page.reload()
    page.wait_for_selector("#groups .group[data-id='m2']")
    page.check("#hide-done")
    page.wait_for_selector("#groups .group[data-id='m2']", state="detached")

    # toggle off, and the choice survives a reload
    page.uncheck("#show-groups")
    assert page.locator("#groups .group").count() == 0
    page.reload()
    page.wait_for_selector("#nodes .node[data-id='a']")
    assert not page.is_checked("#show-groups") and page.locator("#groups .group").count() == 0
    page.check("#show-groups")
    page.wait_for_selector("#groups .group[data-id='m1']")
    assert page.js_errors == []
