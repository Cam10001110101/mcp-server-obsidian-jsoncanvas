"""Tests for JSON Canvas node types."""

import pytest

from jsoncanvas import FileNode, GroupNode, LinkNode, TextNode
from jsoncanvas.errors import InvalidNodeError


def test_text_node_to_dict():
    node = TextNode(id="t", x=1, y=2, width=3, height=4, text="hi", color="#abcdef")
    assert node.to_dict() == {
        "id": "t",
        "type": "text",
        "x": 1,
        "y": 2,
        "width": 3,
        "height": 4,
        "color": "#abcdef",
        "text": "hi",
    }


def test_preset_color_is_valid():
    node = TextNode(id="t", x=0, y=0, width=1, height=1, text="x", color="2")
    assert node.color == "2"


@pytest.mark.parametrize("bad", ["#abc", "7", "0", "blue", "#GGGGGG?"])
def test_invalid_color_raises(bad):
    with pytest.raises(InvalidNodeError):
        TextNode(id="t", x=0, y=0, width=1, height=1, text="x", color=bad)


@pytest.mark.parametrize(
    "bad",
    [
        '#"/><g ',  # SVG-attribute breakout shaped, 7 chars, '#'-prefixed
        "#zzzzzz",  # 7 chars, non-hex
        "# fffff",  # 7 chars, contains a space
        '#"onx="',  # 7 chars, quote + attribute-ish
    ],
)
def test_non_hex_seven_char_color_rejected(bad):
    # Previously len==7 + startswith('#') passed; the strict hex rule now rejects
    # these so they can never reach the (unescaped-by-design) SVG export.
    assert len(bad) == 7 and bad.startswith("#")
    with pytest.raises(InvalidNodeError):
        TextNode(id="t", x=0, y=0, width=1, height=1, text="x", color=bad)


def test_hex_color_accepts_upper_and_lower_case():
    for good in ("#ABCDEF", "#abcdef", "#012345"):
        assert TextNode(id="t", x=0, y=0, width=1, height=1, text="x", color=good)


def test_file_node_subpath_must_start_with_hash():
    with pytest.raises(InvalidNodeError):
        FileNode(id="f", x=0, y=0, width=1, height=1, file="a.md", subpath="nope")
    ok = FileNode(id="f", x=0, y=0, width=1, height=1, file="a.md", subpath="#h")
    assert ok.to_dict()["subpath"] == "#h"


def test_link_node_to_dict_has_url():
    node = LinkNode(id="l", x=0, y=0, width=1, height=1, url="https://example.com")
    assert node.to_dict()["url"] == "https://example.com"


def test_group_node_invalid_background_style_raises():
    with pytest.raises(InvalidNodeError):
        GroupNode(id="g", x=0, y=0, width=1, height=1, background_style="tile")
    ok = GroupNode(id="g", x=0, y=0, width=1, height=1, background_style="cover")
    assert ok.to_dict()["backgroundStyle"] == "cover"
