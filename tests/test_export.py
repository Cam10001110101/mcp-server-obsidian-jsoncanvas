"""Tests for the canvas exporters."""

from jsoncanvas import Canvas, Edge, GroupNode, LinkNode, TextNode
from jsoncanvas.export import to_markdown, to_svg


def _sample() -> Canvas:
    canvas = Canvas()
    canvas.add_node(
        TextNode(id="root", x=0, y=0, width=200, height=100, text="# Title\n\nIntro")
    )
    canvas.add_node(
        TextNode(id="child", x=0, y=200, width=200, height=100, text="## Child\n\nBody")
    )
    canvas.add_node(
        GroupNode(id="grp", x=-20, y=180, width=300, height=160, label="Group A")
    )
    canvas.add_node(
        LinkNode(id="lnk", x=300, y=0, width=150, height=60, url="https://example.com")
    )
    canvas.add_edge(Edge(id="e1", from_node="root", to_node="child", label="leads to"))
    return canvas


def test_to_markdown_includes_titles_body_and_connections():
    md = to_markdown(_sample(), title="Demo")
    assert md.startswith("# Demo")
    assert "## Title" in md  # heading derived from first text line, '#' stripped
    assert "Intro" in md  # body preserved
    assert "## Connections" in md
    assert "Title → Child — leads to" in md
    # Root is ordered before its child (edge-ordered DFS).
    assert md.index("## Title") < md.index("## Child")


def test_to_markdown_handles_cycles_without_infinite_loop():
    canvas = Canvas()
    canvas.add_node(TextNode(id="a", x=0, y=0, width=10, height=10, text="A"))
    canvas.add_node(TextNode(id="b", x=20, y=0, width=10, height=10, text="B"))
    canvas.add_edge(Edge(id="e1", from_node="a", to_node="b"))
    canvas.add_edge(Edge(id="e2", from_node="b", to_node="a"))
    md = to_markdown(canvas)
    assert "## A" in md and "## B" in md


def test_to_svg_is_well_formed():
    svg = to_svg(_sample())
    assert svg.startswith("<svg") and svg.rstrip().endswith("</svg>")
    assert "<rect" in svg and "<path" in svg  # nodes and an edge
    assert "<marker" in svg  # arrowhead
    assert "stroke-dasharray" in svg  # group node drawn dashed
    assert "leads to" in svg  # edge label rendered


def test_to_svg_escapes_text():
    canvas = Canvas()
    canvas.add_node(
        TextNode(id="x", x=0, y=0, width=200, height=80, text="a < b & c > d")
    )
    svg = to_svg(canvas)
    assert "&lt;" in svg and "&amp;" in svg and "&gt;" in svg
    assert "a < b" not in svg  # raw angle brackets must be escaped


def test_to_svg_empty_canvas():
    svg = to_svg(Canvas())
    assert svg.startswith("<svg") and "Empty canvas" in svg
