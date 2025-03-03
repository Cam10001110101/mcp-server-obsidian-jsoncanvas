# JSON Canvas Project

This project provides a Python library for working with JSON Canvas data structures according to the [official specification](https://jsoncanvas.org/spec/1.0/). It uses `uv` for Python package management and will be extended with a Model Context Protocol (MCP) server.

## What is JSON Canvas?

JSON Canvas is an open file format for infinite canvas data. It was originally created for [Obsidian](https://obsidian.md/blog/json-canvas/) and is designed to provide longevity, readability, interoperability, and extensibility to data created with infinite canvas apps.

Infinite canvas tools are a way to view and organize information spatially, like a digital whiteboard. JSON Canvas files use the `.canvas` extension and follow a specific JSON structure.

## Project Components

This project consists of several components:

1. **Python Library** - A library for working with JSON Canvas files
2. **MCP Server** - A Model Context Protocol server for JSON Canvas operations
3. **Examples** - Sample code demonstrating usage
4. **Tests** - Unit tests for the library

## Architecture

The project follows a modular architecture:

- `jsoncanvas/` - Main package directory
  - `__init__.py` - Package initialization
  - `canvas.py` - Core Canvas class implementation (to be updated to match spec)
  - `nodes.py` - Node implementations (to be added)
  - `edges.py` - Edge implementations (to be added)
  - `validation.py` - Schema validation (to be added)
- `tests/` - Test directory
  - `test_canvas.py` - Tests for the Canvas class
  - `test_nodes.py` - Tests for nodes (to be added)
  - `test_edges.py` - Tests for edges (to be added)
- `examples/` - Example scripts
  - `create_canvas.py` - Example of creating a canvas
- `mcp/` - MCP server implementation (to be added)

## Development Workflow

This project uses `uv` for Python package management. The workflow is:

1. Create a virtual environment: `uv venv`
2. Install dependencies: `uv pip install -r requirements.txt`
3. Install development dependencies: `uv pip install -e ".[dev]"`
4. Run tests: `pytest`

## Key Components

### Canvas Class

The Canvas class will be updated to match the official JSON Canvas specification with:

- Support for nodes (text, file, link, group)
- Support for edges between nodes
- Color handling
- Validation against the specification

### MCP Server

The MCP server will provide tools for:

- Validating JSON Canvas files
- Creating and manipulating canvas elements
- Converting between formats
- Analyzing canvas structure
- Generating visualizations

See [mcp-server.md](mcp-server.md) for more details.

### JSON Canvas Specification

The project follows the JSON Canvas 1.0 specification. See [specification.md](specification.md) for details.

### Project Documentation

This project uses dotcontext for managing project documentation and context. The `.context` directory contains structured documentation about the project's architecture, components, and implementation details. See [dotcontext.md](dotcontext.md) for more information about how dotcontext is used in this project.

## Implementation Plan

1. Update the Python library to match the specification
2. Implement validation using JSON Schema
3. Create the MCP server
4. Add examples and documentation
5. Implement advanced features

## Future Development

Planned features include:
- JSON schema validation for canvas elements
- Export to different formats (SVG, PNG)
- Canvas manipulation operations (resize, transform)
- Real-time collaboration features
- Integration with existing canvas tools
