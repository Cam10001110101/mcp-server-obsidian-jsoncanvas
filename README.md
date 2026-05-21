# JSON Canvas MCP Server

A [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server for working with
[JSON Canvas](https://jsoncanvas.org/spec/1.0/) files — the open infinite-canvas format used
by [Obsidian](https://obsidian.md/blog/json-canvas/). It lets an MCP client create, validate,
read, and list `.canvas` files.

Built on the official `mcp` Python SDK (`>=1.27`), which negotiates the **2025-11-25** MCP
protocol revision. Runs over **stdio** by default and optionally over the **Streamable HTTP**
transport.

## Components

### Tools

- **create_canvas** — Create a canvas from `nodes` (and optional `edges`) and write it to a
  date-prefixed `.canvas` file under `OUTPUT_PATH`.
  - Input: `nodes` (array of JSON Canvas node objects), `filename` (string, no extension),
    `edges` (optional array of edge objects).
  - Returns (structured): `{ path, node_count, edge_count }`.
- **validate_canvas** — Validate canvas data against the JSON Canvas 1.0 specification.
  - Input: `canvas` (object with optional `nodes` and `edges`).
  - Returns (structured): `{ valid, error }`.
- **read_canvas** — Read a stored `.canvas` file and return its JSON text.
  - Input: `filename` (string, with or without the `.canvas` extension).
- **list_canvases** — List the `.canvas` files available in `OUTPUT_PATH`.
  - Returns: array of filenames.

Node objects use the JSON Canvas shape: `id`, `type` (`text` | `file` | `link` | `group`),
`x`, `y`, `width`, `height`, optional `color`, plus type-specific fields (`text`, `file`/`subpath`,
`url`, `label`/`background`/`backgroundStyle`). Edge objects use `id`, `fromNode`, `toNode`, and
optional `fromSide`/`toSide`/`fromEnd`/`toEnd`/`color`/`label`.

### Resources

- `canvas://schema` — JSON Schema for validating canvas files.
- `canvas://examples/basic` — A simple example canvas (two text nodes joined by an edge).

## Usage with Claude Desktop

### Docker (stdio)

```bash
docker build -t mcp/jsoncanvas .
```

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "jsoncanvas": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-v", "canvas-data:/data", "mcp/jsoncanvas"],
      "env": { "OUTPUT_PATH": "/data/output" }
    }
  }
}
```

### uv (stdio)

```json
{
  "mcpServers": {
    "jsoncanvas": {
      "command": "uv",
      "args": ["--directory", "/path/to/jsoncanvas", "run", "mcp-server-jsoncanvas"],
      "env": { "OUTPUT_PATH": "./output" }
    }
  }
}
```

## Streamable HTTP transport

To serve over Streamable HTTP instead of stdio:

```bash
mcp-server-jsoncanvas --transport streamable-http --host 127.0.0.1 --port 8000
```

The MCP endpoint is then `http://127.0.0.1:8000/mcp`. The transport binds to localhost and, per
the 2025-11-25 spec, validates the `Origin` header with DNS-rebinding protection enabled
(localhost Origins only by default). To accept connections from outside the host (e.g. when
running the container with HTTP), bind `--host 0.0.0.0` and configure your allowed Origins
accordingly.

## Configuration

Environment variables:

- `OUTPUT_PATH` — Directory where `.canvas` files are written/read (default `./output`).
- `MCP_TRANSPORT` — `stdio` (default) or `streamable-http`.
- `MCP_HOST` / `MCP_PORT` — Host/port for the Streamable HTTP transport (default `127.0.0.1:8000`).

## Development

```bash
# Install uv: https://docs.astral.sh/uv/getting-started/installation/
make setup        # uv venv && uv sync --extra dev
make test         # run the test suite
make lint         # ruff check + format check
make audit        # scan dependencies for known vulnerabilities (pip-audit)
make run          # run the server over stdio
```

Run the bundled library example:

```bash
make example      # writes example.canvas to OUTPUT_PATH (default ./output)
```

## Library example

The `jsoncanvas` package can also be used directly:

```python
from jsoncanvas import Canvas, TextNode, Edge

title = TextNode(id="title", x=100, y=100, width=400, height=100,
                 text="# Hello Canvas", color="#4285F4")
info = TextNode(id="info", x=600, y=100, width=300, height=100,
                text="More information here", color="2")  # preset color

canvas = Canvas()
canvas.add_node(title)
canvas.add_node(info)
canvas.add_edge(Edge(id="edge1", from_node="title", to_node="info",
                     from_side="right", to_side="left", label="Connection"))

import json
print(json.dumps(canvas.to_dict(), indent=2))
```

## License

MIT. See [LICENSE](LICENSE).
