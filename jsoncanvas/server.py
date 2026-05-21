#!/usr/bin/env python3
"""MCP server for JSON Canvas files.

Built on the FastMCP API of the official ``mcp`` SDK, which negotiates the
2025-11-25 Model Context Protocol revision. Exposes four tools (create, validate,
read, list) and two resources (schema, example) over either stdio (default) or
the Streamable HTTP transport.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

from jsoncanvas import (
    Canvas,
    Edge,
    FileNode,
    GroupNode,
    LinkNode,
    TextNode,
    __version__,
)


# --------------------------------------------------------------------------- #
# Structured tool outputs (emitted as outputSchema + structured content)
# --------------------------------------------------------------------------- #
class CreateCanvasResult(BaseModel):
    """Result of writing a canvas to disk."""

    path: str = Field(description="Absolute path to the written .canvas file")
    node_count: int = Field(description="Number of nodes written")
    edge_count: int = Field(description="Number of edges written")


class ValidateCanvasResult(BaseModel):
    """Result of validating canvas data against the JSON Canvas 1.0 spec."""

    valid: bool = Field(description="True when the canvas conforms to the spec")
    error: str | None = Field(
        default=None, description="Validation error message when invalid"
    )


# --------------------------------------------------------------------------- #
# Server
# --------------------------------------------------------------------------- #
# FastMCP defaults already enable DNS-rebinding protection and restrict the
# Streamable HTTP transport to localhost Origins/Hosts (127.0.0.1:*, localhost:*,
# [::1]:*), which satisfies the 2025-11-25 Origin-validation requirement.
mcp = FastMCP(
    "jsoncanvas",
    instructions=(
        "Tools for creating, validating, reading, and listing JSON Canvas "
        "(.canvas) files following the JSON Canvas 1.0 specification. Files are "
        "written to and read from the directory named by the OUTPUT_PATH "
        "environment variable (default ./output)."
    ),
)
# FastMCP defaults serverInfo.version to the SDK version; report our own instead.
mcp._mcp_server.version = __version__

_NODE_TYPES: dict[str, type] = {
    "text": TextNode,
    "file": FileNode,
    "link": LinkNode,
    "group": GroupNode,
}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _output_dir() -> Path:
    """Return the configured output directory, creating it if needed."""
    path = Path(os.environ.get("OUTPUT_PATH", "./output"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe_target(filename: str) -> Path:
    """Resolve ``filename`` to a ``.canvas`` path inside the output directory.

    Strips any directory components and rejects values that would escape the
    output directory (path traversal / symlink escape).
    """
    name = Path(filename).name
    if not name or name in {".", ".."}:
        raise ValueError("Invalid filename")
    if not name.endswith(".canvas"):
        name += ".canvas"
    out = _output_dir().resolve()
    target = (out / name).resolve()
    if target.parent != out:
        raise ValueError("Filename must not escape the output directory")
    return target


def _build_canvas(
    nodes: list[dict[str, Any]], edges: list[dict[str, Any]] | None
) -> Canvas:
    """Build and validate a :class:`Canvas` from JSON Canvas node/edge dicts."""
    canvas = Canvas()
    for node_data in nodes:
        data = dict(node_data)  # copy so caller input is not mutated
        node_type = data.pop("type", None)
        node_cls = _NODE_TYPES.get(node_type)
        if node_cls is None:
            raise ValueError(f"Unknown node type: {node_type!r}")
        # JSON Canvas uses camelCase "backgroundStyle"; the model expects snake_case.
        if node_type == "group" and "backgroundStyle" in data:
            data["background_style"] = data.pop("backgroundStyle")
        canvas.add_node(node_cls(**data))
    for edge_data in edges or []:
        canvas.add_edge(Edge.from_dict(edge_data))
    return canvas


# --------------------------------------------------------------------------- #
# Tools
# --------------------------------------------------------------------------- #
@mcp.tool(
    title="Create Canvas",
    description=(
        "Create a JSON Canvas from nodes (and optional edges) and write it as a "
        "date-prefixed .canvas file under OUTPUT_PATH."
    ),
)
def create_canvas(
    nodes: list[dict[str, Any]],
    filename: str,
    edges: list[dict[str, Any]] | None = None,
) -> CreateCanvasResult:
    """Create a canvas and persist it.

    Args:
        nodes: JSON Canvas node objects. Each requires ``id``, ``type``
            (text/file/link/group), ``x``, ``y``, ``width``, ``height`` plus
            type-specific fields (``text``, ``file``, ``url``, ...).
        filename: Output name (without extension); a ``YYYY-MM-DD-`` prefix and
            ``.canvas`` extension are added automatically.
        edges: Optional JSON Canvas edge objects (``id``, ``fromNode``, ``toNode``,
            and optional ``fromSide``/``toSide``/``color``/``label``).
    """
    canvas = _build_canvas(nodes, edges)
    date_prefix = datetime.now().strftime("%Y-%m-%d")
    target = _safe_target(f"{date_prefix}-{filename}")
    target.write_text(json.dumps(canvas.to_dict(), indent=2))
    print(f"Wrote canvas to {target}", file=sys.stderr)
    return CreateCanvasResult(
        path=str(target),
        node_count=len(canvas.nodes),
        edge_count=len(canvas.edges),
    )


@mcp.tool(
    title="Validate Canvas",
    description="Validate canvas data against the JSON Canvas 1.0 specification.",
)
def validate_canvas(canvas: dict[str, Any]) -> ValidateCanvasResult:
    """Validate canvas data and report whether it conforms to the spec.

    Args:
        canvas: A canvas object with optional ``nodes`` and ``edges`` arrays.
    """
    try:
        Canvas.from_dict(canvas)
    except Exception as exc:  # noqa: BLE001 - surface any validation failure
        return ValidateCanvasResult(valid=False, error=str(exc))
    return ValidateCanvasResult(valid=True)


@mcp.tool(
    title="Read Canvas",
    description="Read a .canvas file from OUTPUT_PATH and return its JSON text.",
)
def read_canvas(filename: str) -> str:
    """Return the JSON text of a stored canvas.

    Args:
        filename: Name of the canvas file under OUTPUT_PATH (with or without the
            ``.canvas`` extension).
    """
    target = _safe_target(filename)
    if not target.is_file():
        raise ValueError(f"Canvas not found: {target.name}")
    return target.read_text()


@mcp.tool(
    title="List Canvases",
    description="List the .canvas files available in OUTPUT_PATH.",
)
def list_canvases() -> list[str]:
    """Return the names of ``.canvas`` files in the output directory."""
    return sorted(p.name for p in _output_dir().glob("*.canvas"))


# --------------------------------------------------------------------------- #
# Resources
# --------------------------------------------------------------------------- #
_CANVAS_SCHEMA: dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "JSON Canvas",
    "type": "object",
    "properties": {
        "nodes": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "type", "x", "y", "width", "height"],
                "properties": {
                    "id": {"type": "string"},
                    "type": {
                        "type": "string",
                        "enum": ["text", "file", "link", "group"],
                    },
                    "x": {"type": "number"},
                    "y": {"type": "number"},
                    "width": {"type": "number"},
                    "height": {"type": "number"},
                    "color": {"type": "string"},
                },
            },
        },
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "fromNode", "toNode"],
                "properties": {
                    "id": {"type": "string"},
                    "fromNode": {"type": "string"},
                    "toNode": {"type": "string"},
                    "fromSide": {
                        "type": "string",
                        "enum": ["top", "right", "bottom", "left"],
                    },
                    "toSide": {
                        "type": "string",
                        "enum": ["top", "right", "bottom", "left"],
                    },
                    "fromEnd": {"type": "string", "enum": ["none", "arrow"]},
                    "toEnd": {"type": "string", "enum": ["none", "arrow"]},
                    "color": {"type": "string"},
                    "label": {"type": "string"},
                },
            },
        },
    },
}


@mcp.resource(
    "canvas://schema",
    title="JSON Canvas Schema",
    description="JSON Schema for validating canvas files.",
    mime_type="application/json",
)
def canvas_schema() -> str:
    """Return the JSON Canvas validation schema."""
    return json.dumps(_CANVAS_SCHEMA, indent=2)


@mcp.resource(
    "canvas://examples/basic",
    title="Basic Canvas Example",
    description="A simple canvas with two text nodes connected by an edge.",
    mime_type="application/json",
)
def basic_example() -> str:
    """Return an example canvas demonstrating the basic node and edge types."""
    canvas = Canvas()
    canvas.add_node(
        TextNode(
            id="title",
            x=100,
            y=100,
            width=400,
            height=100,
            text="# Example Canvas\n\nCreated by JSON Canvas MCP Server",
            color="#4285F4",
        )
    )
    canvas.add_node(
        TextNode(
            id="info",
            x=600,
            y=100,
            width=300,
            height=100,
            text="This is a simple example canvas.",
            color="2",
        )
    )
    canvas.add_edge(
        Edge(
            id="edge1",
            from_node="title",
            to_node="info",
            from_side="right",
            to_side="left",
            label="Connection",
        )
    )
    return json.dumps(canvas.to_dict(), indent=2)


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    """Run the JSON Canvas MCP server."""
    parser = argparse.ArgumentParser(
        prog="mcp-server-jsoncanvas",
        description="JSON Canvas MCP server (Model Context Protocol 2025-11-25).",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default=os.environ.get("MCP_TRANSPORT", "stdio"),
        help="Transport to serve on (default: stdio).",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("MCP_HOST", "127.0.0.1"),
        help="Host for the streamable-http transport (default: 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("MCP_PORT", "8000")),
        help="Port for the streamable-http transport (default: 8000).",
    )
    args = parser.parse_args()

    print(f"OUTPUT_PATH={_output_dir()}", file=sys.stderr)
    if args.transport == "streamable-http":
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        print(
            f"Serving Streamable HTTP at http://{args.host}:{args.port}"
            f"{mcp.settings.streamable_http_path}",
            file=sys.stderr,
        )
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
