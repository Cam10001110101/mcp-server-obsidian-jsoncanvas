"""Tests for the MCP server layer."""

import pytest
from mcp.shared.memory import (
    create_connected_server_and_client_session as client_session,
)

from jsoncanvas import server
from jsoncanvas.errors import DuplicateIdError
from jsoncanvas.server import (
    create_canvas,
    edit_canvas,
    export_canvas,
    list_canvases,
    mcp,
    read_canvas,
    search_canvases,
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

    doc = read_canvas(names[0])
    assert doc.nodes[0]["id"] == "a"


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
            "edit_canvas",
            "export_canvas",
            "search_canvases",
        }

        result = await client.call_tool(
            "create_canvas", {"nodes": [TEXT_NODE], "filename": "proto"}
        )
        assert result.isError is False
        assert result.structuredContent["node_count"] == 1


async def test_canvas_viewer_ui_wiring(_output_dir):
    async with client_session(mcp) as client:
        # The viewer is registered with the MCP Apps UI MIME type.
        resources = await client.list_resources()
        viewer = {str(r.uri): r for r in resources.resources}.get(
            "ui://canvas/viewer.html"
        )
        assert viewer is not None
        assert viewer.mimeType == "text/html;profile=mcp-app"

        # read_canvas / create_canvas advertise the viewer via _meta.ui.resourceUri;
        # the plain tools do not.
        by_name = {t.name: t for t in (await client.list_tools()).tools}
        for name in ("read_canvas", "create_canvas"):
            meta = by_name[name].meta or {}
            assert meta.get("ui", {}).get("resourceUri") == "ui://canvas/viewer.html"
        assert by_name["validate_canvas"].meta is None
        assert by_name["list_canvases"].meta is None

        # create_canvas returns the full canvas document for the UI to render.
        created = await client.call_tool(
            "create_canvas", {"nodes": [TEXT_NODE], "filename": "ui"}
        )
        assert created.structuredContent["canvas"]["nodes"][0]["id"] == "a"

        # read_canvas exposes nodes as structured content, and still ships a text
        # fallback for non-UI hosts.
        names = list_canvases()
        read = await client.call_tool("read_canvas", {"filename": names[0]})
        assert read.structuredContent["nodes"][0]["id"] == "a"
        assert "nodes" in read.content[0].text


def test_load_ui_html_returns_bundle():
    html = server._load_ui_html()
    assert "<html" in html.lower()
    assert "</html>" in html.lower()


NODE_B = {**TEXT_NODE, "id": "b", "x": 300, "text": "world"}


def _seed_two_node_canvas() -> str:
    """Create a canvas with nodes a, b and edge e; return its filename."""
    create_canvas(
        nodes=[TEXT_NODE, NODE_B],
        filename="edit",
        edges=[{"id": "e", "fromNode": "a", "toNode": "b"}],
    )
    return list_canvases()[0]


def test_edit_canvas_add_update_remove_round_trip(_output_dir):
    name = _seed_two_node_canvas()
    result = edit_canvas(
        filename=name,
        add_nodes=[{**TEXT_NODE, "id": "c", "x": 600, "text": "third"}],
        update_nodes=[{"id": "a", "text": "edited", "color": "4"}],
        add_edges=[{"id": "e2", "fromNode": "a", "toNode": "c", "label": "to c"}],
        remove_node_ids=["b"],  # cascades edge "e"
    )
    node_ids = {n["id"] for n in result.canvas.nodes}
    edge_ids = {e["id"] for e in result.canvas.edges}
    assert node_ids == {"a", "c"}
    assert edge_ids == {"e2"}  # original edge "e" cascaded away with node "b"
    node_a = next(n for n in result.canvas.nodes if n["id"] == "a")
    assert node_a["text"] == "edited" and node_a["color"] == "4"

    # Persisted to disk.
    on_disk = read_canvas(name)
    assert {n["id"] for n in on_disk.nodes} == {"a", "c"}


def test_edit_canvas_is_atomic_on_error(_output_dir):
    name = _seed_two_node_canvas()
    before = read_canvas(name).model_dump()
    # A duplicate-id add must fail and leave the file untouched.
    with pytest.raises(DuplicateIdError):
        edit_canvas(filename=name, add_nodes=[TEXT_NODE])  # id "a" already exists
    assert read_canvas(name).model_dump() == before


def test_edit_canvas_unknown_id_raises(_output_dir):
    name = _seed_two_node_canvas()
    with pytest.raises(ValueError):
        edit_canvas(filename=name, update_nodes=[{"id": "nope", "text": "x"}])
    with pytest.raises(ValueError):
        edit_canvas(filename=name, remove_edge_ids=["nope"])


async def test_edit_canvas_ui_meta_and_rerender(_output_dir):
    name = _seed_two_node_canvas()
    async with client_session(mcp) as client:
        by_name = {t.name: t for t in (await client.list_tools()).tools}
        meta = by_name["edit_canvas"].meta or {}
        assert meta.get("ui", {}).get("resourceUri") == "ui://canvas/viewer.html"

        result = await client.call_tool(
            "edit_canvas",
            {"filename": name, "update_nodes": [{"id": "a", "text": "changed"}]},
        )
        assert result.isError is False
        node_a = next(
            n for n in result.structuredContent["canvas"]["nodes"] if n["id"] == "a"
        )
        assert node_a["text"] == "changed"


def test_export_canvas_markdown_and_svg(_output_dir):
    name = _seed_two_node_canvas()
    md = export_canvas(filename=name, format="markdown")
    assert md.mime_type == "text/markdown"
    assert "## hello" in md.content and "## Connections" in md.content

    svg = export_canvas(filename=name, format="svg")
    assert svg.mime_type == "image/svg+xml"
    assert svg.content.startswith("<svg") and "<rect" in svg.content


def test_search_canvases_finds_and_misses(_output_dir):
    _seed_two_node_canvas()
    hits = search_canvases(query="world")
    assert len(hits.matches) >= 1
    match = hits.matches[0]
    assert match.kind == "node" and match.id == "b" and match.field == "text"
    assert match.filename.endswith(".canvas")

    assert search_canvases(query="absolutely-not-present").matches == []
