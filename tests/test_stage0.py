"""Stage 0 (PLAN.md): thao tác web trên file 0.3 ghi đúng cú pháp 0.3; kg: lạ báo lỗi; JSON đọc được bằng networkx."""
import pytest

from king_markdown.ops03 import OPS03, Doc03
from king_markdown.parser import Parser

SRC = """---
kg: 0.3
use:
- king/schema.link: needs
---

# Toan @toan

@node a
- label: A
- link needs: (b)  // ghi chú

Nội dung a.

@node b
- label: B

## Con @con

@node c
- label: C
"""


def run(op, text=SRC, **args):
    text, extra = OPS03[op](Doc03(text, "x.kg.md"), **args)
    g = Parser(text, "x.kg.md").build()
    assert g["graph"]["errors"] == [], g["graph"]["errors"]
    return text, g, extra


def ids(g):
    return {n["id"]: n for n in g["nodes"]}


def edges(g):
    return {(l["source"], l["type"], l["target"]) for l in g["links"] if not l.get("tree") and l["type"] != "mention"}


def test_add_node_writes_03_syntax():
    text, g, extra = run("add_node", title="Bê ta", section="con")
    assert "@node be-ta\n- label: Bê ta" in text and "@be-ta:" not in text
    assert ids(g)["be-ta"]["parent"] == "con"


def test_add_node_end_of_file():
    text, g, _ = run("add_node", title="Cuối")
    assert text.rstrip().endswith("- label: Cuối")


def test_rename_node_and_section():
    text, g, _ = run("rename", id="b", title="Bê")
    assert ids(g)["b"]["label"] == "Bê"
    text, g, _ = run("rename", id="con", title="Phần con")
    assert "## Phần con @con" in text


def test_add_link_extends_existing_line_and_keeps_comment():
    text, g, _ = run("add_link", source="a", target="c", type="needs")
    assert "- link needs: (b, c)  // ghi chú" in text
    assert ("a", "needs", "c") in edges(g)


def test_add_link_new_line():
    text, g, _ = run("add_link", source="b", target="c", type="needs")
    assert ("b", "needs", "c") in edges(g)


def test_delete_link_and_last_item_removes_line():
    text, g, _ = run("delete_link", links=[{"source": "a", "target": "b", "type": "needs"}])
    assert "- link needs" not in text and edges(g) == set()


def test_delete_and_move_node():
    text, g, _ = run("delete_node", ids=["b"])
    assert "b" not in ids(g) and "Nội dung a." in text
    text, g, _ = run("move_node", ids=["a"], section="con")
    assert ids(g)["a"]["parent"] == "con" and ("a", "needs", "b") in edges(g)


def test_unsupported_op_refuses_without_writing():
    with pytest.raises(ValueError, match="chưa hỗ trợ"):
        OPS03["set_style"](Doc03(SRC, "x.kg.md"), selectors=[], props={})


def test_unknown_kg_version_is_error():
    g = Parser("---\nkg: 0.9\n---\n\n@node a\n- label: A\n", "x.kg.md").build()
    assert any("0.9" in e["msg"] for e in g["graph"]["errors"])
    g = Parser("---\nkg: 0.3\n---\n\n@node a\n- label: A\n", "x.kg.md").build()
    assert g["graph"]["errors"] == []


def test_json_loads_in_networkx_with_explicit_links_key():
    nx = pytest.importorskip("networkx")
    g = Parser(SRC, "x.kg.md").build()
    G = nx.node_link_graph(g, edges="links")
    assert G.is_directed() and G.is_multigraph()
    assert G.number_of_nodes() == len(g["nodes"]) and G.number_of_edges() == len(g["links"])
    back = nx.node_link_data(G, edges="links")
    assert len(back["links"]) == len(g["links"])


def test_static_html_has_fullscreen_button_and_book_view():
    from king_markdown.cli import static_html
    page = static_html("x.kg.md", "---\nkg: 0.3\n---\n", {"graph": {}, "nodes": [], "links": []})
    assert 'id="bFullscreen"' in page and "requestFullscreen" in page
    assert 'id="bExplorer"' in page
    assert 'setView("book")' in page
