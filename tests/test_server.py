"""Tests for the MCP server layer."""

import json

import pytest
from mcp.shared.memory import (
    create_connected_server_and_client_session as client_session,
)

from jsoncanvas import server
from jsoncanvas.server import (
    create_canvas,
    list_canvases,
    mcp,
    read_canvas,
    validate_canvas,
)

TEXT_NODE = {
    "id": "a",
    "type": "text",
    "x": 0,
    "y": 0,
    "width": 100,
    "height": 50,
    "text": "hello",
}


@pytest.fixture(autouse=True)
def _output_dir(tmp_path, monkeypatch):
    """Point OUTPUT_PATH at a temp dir for every test."""
    monkeypatch.setenv("OUTPUT_PATH", str(tmp_path))
    return tmp_path


def test_create_read_list_round_trip(_output_dir):
    result = create_canvas(nodes=[TEXT_NODE], filename="demo")
    assert result.node_count == 1
    assert result.edge_count == 0
    written = _output_dir / result.path.split("/")[-1]
    assert written.exists()

    names = list_canvases()
    assert len(names) == 1
    assert names[0].endswith("-demo.canvas")

    text = read_canvas(names[0])
    assert json.loads(text)["nodes"][0]["id"] == "a"


def test_create_with_edges_and_group_background_style(_output_dir):
    nodes = [
        TEXT_NODE,
        {
            "id": "b",
            "type": "text",
            "x": 200,
            "y": 0,
            "width": 100,
            "height": 50,
            "text": "b",
        },
        {
            "id": "g",
            "type": "group",
            "x": 0,
            "y": 0,
            "width": 400,
            "height": 200,
            "label": "grp",
            "backgroundStyle": "cover",
        },
    ]
    edges = [{"id": "e", "fromNode": "a", "toNode": "b", "fromSide": "right"}]
    result = create_canvas(nodes=nodes, filename="withedges", edges=edges)
    assert result.node_count == 3
    assert result.edge_count == 1


def test_validate_valid_and_invalid():
    assert validate_canvas({"nodes": [TEXT_NODE]}).valid is True

    bad = validate_canvas(
        {
            "nodes": [
                {"id": "x", "type": "widget", "x": 0, "y": 0, "width": 1, "height": 1}
            ]
        }
    )
    assert bad.valid is False
    assert bad.error


def test_filename_traversal_is_neutralized(_output_dir):
    # Directory components are stripped; the file cannot escape OUTPUT_PATH.
    result = create_canvas(nodes=[TEXT_NODE], filename="../../evil")
    written = server._output_dir().resolve()
    assert (written / result.path.split("/")[-1]).parent == written
    # Nothing was written outside the output directory.
    assert not (_output_dir.parent / "evil.canvas").exists()


def test_invalid_filename_rejected():
    with pytest.raises(ValueError):
        read_canvas("..")


def test_read_missing_canvas_raises():
    with pytest.raises(ValueError):
        read_canvas("does-not-exist")


async def test_tools_exposed_over_protocol(_output_dir):
    async with client_session(mcp) as client:
        listed = await client.list_tools()
        names = {tool.name for tool in listed.tools}
        assert names == {
            "create_canvas",
            "validate_canvas",
            "read_canvas",
            "list_canvases",
        }

        result = await client.call_tool(
            "create_canvas", {"nodes": [TEXT_NODE], "filename": "proto"}
        )
        assert result.isError is False
        assert result.structuredContent["node_count"] == 1
