"""Tests for the Canvas container."""

import pytest

from jsoncanvas import Canvas, Edge, TextNode
from jsoncanvas.errors import DuplicateIdError, ReferenceError, ValidationError


def _node(node_id: str) -> TextNode:
    return TextNode(id=node_id, x=0, y=0, width=10, height=10, text=node_id)


def test_duplicate_node_id_raises():
    canvas = Canvas()
    canvas.add_node(_node("a"))
    with pytest.raises(DuplicateIdError):
        canvas.add_node(_node("a"))


def test_edge_referencing_missing_node_raises():
    canvas = Canvas()
    canvas.add_node(_node("a"))
    with pytest.raises(ReferenceError):
        canvas.add_edge(Edge(id="e", from_node="a", to_node="ghost"))


def test_to_dict_from_dict_round_trip():
    canvas = Canvas()
    canvas.add_node(_node("a"))
    canvas.add_node(_node("b"))
    canvas.add_edge(Edge(id="e", from_node="a", to_node="b", from_side="right"))

    restored = Canvas.from_dict(canvas.to_dict())
    assert {n.id for n in restored.nodes} == {"a", "b"}
    assert restored.edges[0].from_node == "a"
    assert restored.edges[0].to_node == "b"


def test_from_dict_unknown_node_type_raises():
    with pytest.raises(ValidationError):
        Canvas.from_dict(
            {
                "nodes": [
                    {
                        "id": "x",
                        "type": "widget",
                        "x": 0,
                        "y": 0,
                        "width": 1,
                        "height": 1,
                    }
                ]
            }
        )


def test_empty_canvas_is_valid():
    # nodes and edges are both optional in the JSON Canvas spec.
    canvas = Canvas.from_dict({})
    assert canvas.nodes == []
    assert canvas.edges == []


def test_update_node_replaces_in_place_and_keeps_edges():
    canvas = Canvas()
    canvas.add_node(_node("a"))
    canvas.add_node(_node("b"))
    canvas.add_edge(Edge(id="e", from_node="a", to_node="b"))

    old = canvas.update_node(
        TextNode(id="a", x=5, y=5, width=20, height=20, text="new", color="4")
    )
    assert old.text == "a"
    assert canvas.get_node("a").text == "new"
    assert canvas.get_node("a").color == "4"
    # Edge survives (unlike remove_node, which cascades).
    assert len(canvas.edges) == 1


def test_update_node_unknown_id_raises():
    canvas = Canvas()
    canvas.add_node(_node("a"))
    with pytest.raises(ReferenceError):
        canvas.update_node(_node("missing"))


def test_update_edge_replaces_and_validates_references():
    canvas = Canvas()
    canvas.add_node(_node("a"))
    canvas.add_node(_node("b"))
    canvas.add_edge(Edge(id="e", from_node="a", to_node="b"))

    canvas.update_edge(Edge(id="e", from_node="a", to_node="b", label="link"))
    assert canvas.get_edge("e").label == "link"

    with pytest.raises(ReferenceError):
        canvas.update_edge(Edge(id="e", from_node="a", to_node="ghost"))
    with pytest.raises(ReferenceError):
        canvas.update_edge(Edge(id="missing", from_node="a", to_node="b"))
