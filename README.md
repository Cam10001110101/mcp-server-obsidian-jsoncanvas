# JSON Canvas MCP Server

A Model Context Protocol (MCP) server implementation that provides tools for working with JSON Canvas files according to the [official specification](https://jsoncanvas.org/spec/1.0/). This server enables creating, modifying, and validating infinite canvas data structures.

## Overview

The JSON Canvas MCP server provides a complete implementation of the JSON Canvas 1.0 specification, enabling:

- Creation and manipulation of infinite canvas data
- Support for all node types (text, file, link, group)
- Edge connections with styling and labels
- Validation against the specification
- Configurable output paths

## Components

### Resources

The server exposes the following resources:

- `canvas://schema`: JSON Schema for validating canvas files
- `canvas://examples`: Example canvas files demonstrating different features
- `canvas://templates`: Templates for creating new canvases

### Tools

#### Node Operations

- **create_node**
  - Create a new node of any supported type
  - Input:
    - `type` (string): Node type ("text", "file", "link", "group")
    - `properties` (object): Node-specific properties
      - Common: `id`, `x`, `y`, `width`, `height`, `color`
      - Type-specific: `text`, `file`, `url`, etc.
  - Returns: Created node object

- **update_node**
  - Update an existing node's properties
  - Input:
    - `id` (string): Node ID to update
    - `properties` (object): Properties to update
  - Returns: Updated node object

- **delete_node**
  - Remove a node and its connected edges
  - Input:
    - `id` (string): Node ID to delete
  - Returns: Success confirmation

#### Edge Operations

- **create_edge**
  - Create a new edge between nodes
  - Input:
    - `id` (string): Unique edge identifier
    - `fromNode` (string): Source node ID
    - `toNode` (string): Target node ID
    - `fromSide` (optional string): Start side ("top", "right", "bottom", "left")
    - `toSide` (optional string): End side
    - `color` (optional string): Edge color
    - `label` (optional string): Edge label
  - Returns: Created edge object

- **update_edge**
  - Update an existing edge's properties
  - Input:
    - `id` (string): Edge ID to update
    - `properties` (object): Properties to update
  - Returns: Updated edge object

- **delete_edge**
  - Remove an edge
  - Input:
    - `id` (string): Edge ID to delete
  - Returns: Success confirmation

#### Canvas Operations

- **validate_canvas**
  - Validate a canvas against the specification
  - Input:
    - `canvas` (object): Canvas data to validate
  - Returns: Validation results with any errors

- **export_canvas**
  - Export canvas to different formats
  - Input:
    - `format` (string): Target format ("json", "svg", "png")
    - `canvas` (object): Canvas data to export
  - Returns: Exported canvas in requested format

## Usage with Claude Desktop

### Docker

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "jsoncanvas": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v",
        "canvas-data:/data",
        "mcp/jsoncanvas"
      ],
      "env": {
        "OUTPUT_PATH": "/data/output"
      }
    }
  }
}
```

### UV

```json
{
  "mcpServers": {
    "jsoncanvas": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/jsoncanvas",
        "run",
        "mcp-server-jsoncanvas"
      ],
      "env": {
        "OUTPUT_PATH": "./output"
      }
    }
  }
}
```

## Configuration

The server can be configured using environment variables:

- `OUTPUT_PATH`: Directory where canvas files will be saved (default: "./output")
- `FORMAT`: Default output format for canvas files (default: "json")

## Building

### Docker Build

```bash
docker build -t mcp/jsoncanvas .
```

### Local Build

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .

# Run tests
pytest
```

## Example Usage

### Creating a Canvas

```python
from jsoncanvas import Canvas, TextNode, Edge

# Create nodes
title = TextNode(
    id="title",
    x=100,
    y=100,
    width=400,
    height=100,
    text="# Hello Canvas\n\nThis is a demonstration.",
    color="#4285F4"
)

info = TextNode(
    id="info",
    x=600,
    y=100,
    width=300,
    height=100,
    text="More information here",
    color="2"  # Using preset color
)

# Create canvas
canvas = Canvas()
canvas.add_node(title)
canvas.add_node(info)

# Connect nodes
edge = Edge(
    id="edge1",
    from_node="title",
    to_node="info",
    from_side="right",
    to_side="left",
    label="Connection"
)
canvas.add_edge(edge)

# Save canvas
canvas.save("example.canvas")
```

## License

This MCP server is licensed under the MIT License. This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the MIT License. For more details, please see the LICENSE file in the project repository.
