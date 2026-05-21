"""Tests for JSON Canvas edges."""

import pytest

from jsoncanvas import Edge
from jsoncanvas.errors import InvalidEdgeError


def test_edge_defaults_and_to_dict():
    edge = Edge(id="e", from_node="a", to_node="b")
    d = edge.to_dict()
    assert d["fromNode"] == "a"
    assert d["toNode"] == "b"
    # Spec defaults: from end "none", to end "arrow".
    assert d["fromEnd"] == "none"
    assert d["toEnd"] == "arrow"
    # Optional fields omitted when unset.
    assert "fromSide" not in d
    assert "label" not in d


def test_edge_round_trip_from_dict():
    src = {
        "id": "e",
        "fromNode": "a",
        "toNode": "b",
        "fromSide": "right",
        "toSide": "left",
        "color": "3",
        "label": "link",
    }
    edge = Edge.from_dict(src)
    out = edge.to_dict()
    for key, value in src.items():
        assert out[key] == value


def test_invalid_side_raises():
    with pytest.raises(InvalidEdgeError):
        Edge(id="e", from_node="a", to_node="b", from_side="sideways")


def test_invalid_end_raises():
    with pytest.raises(InvalidEdgeError):
        Edge(id="e", from_node="a", to_node="b", to_end="circle")
