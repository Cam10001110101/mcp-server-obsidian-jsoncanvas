#!/usr/bin/env python3
"""MCP server for JSON Canvas."""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    JSONRPCError,
    ListResourcesRequest,
    ListToolsRequest,
    ReadResourceRequest,
)

from jsoncanvas import (
    Canvas,
    TextNode,
    FileNode,
    LinkNode,
    GroupNode,
    Edge,
)


class JSONCanvasServer:
    """MCP server for JSON Canvas."""

    def __init__(self):
        """Initialize the server."""
        self.server = Server(
            {
                "name": "jsoncanvas",
                "version": "0.1.0",
            },
            {
                "capabilities": {
                    "resources": {},
                    "tools": {},
                },
            },
        )

        # Get output path from environment variable or use default
        output_path = os.environ.get("OUTPUT_PATH", "./output")
        self.output_path = Path(output_path)
        
        # Print the output path for debugging
        print(f"Output path: {self.output_path}", file=sys.stderr)
        
        # Create the output directory if it doesn't exist
        self.output_path.mkdir(parents=True, exist_ok=True)

        # Set up handlers
        self.setup_resource_handlers()
        self.setup_tool_handlers()

        # Error handling
        self.server.onerror = lambda error: print(f"[MCP Error] {error}", file=sys.stderr)
        
    def setup_resource_handlers(self):
        """Set up resource handlers."""
        self.server.request_handlers[ListResourcesRequest] = self.handle_list_resources
        self.server.request_handlers[ReadResourceRequest] = self.handle_read_resource

    def setup_tool_handlers(self):
        """Set up tool handlers."""
        self.server.request_handlers[ListToolsRequest] = self.handle_list_tools
        self.server.request_handlers[CallToolRequest] = self.handle_call_tool

    async def handle_list_resources(self, request):
        """Handle list resources request."""
        return {
            "resources": [
                {
                    "uri": "canvas://schema",
                    "name": "JSON Canvas Schema",
                    "mimeType": "application/json",
                    "description": "JSON Schema for validating canvas files",
                },
                {
                    "uri": "canvas://examples/basic",
                    "name": "Basic Canvas Example",
                    "mimeType": "application/json",
                    "description": "A simple canvas with basic node types",
                },
            ],
        }

    async def handle_read_resource(self, request):
        """Handle read resource request."""
        uri = request.params.uri
        
        if uri == "canvas://schema":
            # Return the JSON Canvas schema
            schema = {
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
                                "type": {"type": "string", "enum": ["text", "file", "link", "group"]},
                                "x": {"type": "number"},
                                "y": {"type": "number"},
                                "width": {"type": "number"},
                                "height": {"type": "number"},
                                "color": {"type": "string"}
                            }
                        }
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
                                "fromSide": {"type": "string", "enum": ["top", "right", "bottom", "left"]},
                                "toSide": {"type": "string", "enum": ["top", "right", "bottom", "left"]},
                                "fromEnd": {"type": "string", "enum": ["none", "arrow"]},
                                "toEnd": {"type": "string", "enum": ["none", "arrow"]},
                                "color": {"type": "string"},
                                "label": {"type": "string"}
                            }
                        }
                    }
                }
            }
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(schema, indent=2),
                    }
                ]
            }
        elif uri == "canvas://examples/basic":
            # Create a basic example canvas
            canvas = Canvas()
            
            # Add nodes
            title = TextNode(
                id="title",
                x=100,
                y=100,
                width=400,
                height=100,
                text="# Example Canvas\n\nCreated by JSON Canvas MCP Server",
                color="#4285F4"
            )
            
            info = TextNode(
                id="info",
                x=600,
                y=100,
                width=300,
                height=100,
                text="This is a simple example canvas.",
                color="2"
            )
            
            canvas.add_node(title)
            canvas.add_node(info)
            
            # Add edge
            edge = Edge(
                id="edge1",
                from_node="title",
                to_node="info",
                from_side="right",
                to_side="left",
                label="Connection"
            )
            canvas.add_edge(edge)
            
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(canvas.to_dict(), indent=2),
                    }
                ]
            }
        else:
            raise JSONRPCError(
                code=400,
                message=f"Unknown resource: {uri}"
            )

    async def handle_list_tools(self, request):
        """Handle list tools request."""
        return {
            "tools": [
                {
                    "name": "create_canvas",
                    "description": "Create a new canvas with specified nodes and edges",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "nodes": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["id", "type", "x", "y", "width", "height"],
                                }
                            },
                            "edges": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["id", "fromNode", "toNode"],
                                }
                            },
                            "filename": {
                                "type": "string",
                                "description": "Output filename (without extension)"
                            }
                        },
                        "required": ["nodes", "filename"]
                    }
                },
                {
                    "name": "validate_canvas",
                    "description": "Validate a canvas against the JSON Canvas specification",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "canvas": {
                                "type": "object",
                                "description": "Canvas data to validate"
                            }
                        },
                        "required": ["canvas"]
                    }
                }
            ]
        }

    async def handle_call_tool(self, request):
        """Handle call tool request."""
        tool_name = request.params.name
        args = request.params.arguments
        
        if tool_name == "create_canvas":
            try:
                # Create a new canvas
                canvas = Canvas()
                
                # Add nodes
                for node_data in args["nodes"]:
                    node_type = node_data.pop("type")
                    if node_type == "text":
                        node = TextNode(**node_data)
                    elif node_type == "file":
                        node = FileNode(**node_data)
                    elif node_type == "link":
                        node = LinkNode(**node_data)
                    elif node_type == "group":
                        node = GroupNode(**node_data)
                    else:
                        raise ValueError(f"Unknown node type: {node_type}")
                    
                    canvas.add_node(node)
                
                # Add edges if provided
                if "edges" in args:
                    for edge_data in args["edges"]:
                        edge = Edge(**edge_data)
                        canvas.add_edge(edge)
                
                # Add date prefix to filename to avoid overwriting
                date_prefix = datetime.now().strftime("%Y-%m-%d")
                filename = args["filename"]
                output_file = self.output_path / f"{date_prefix}-{filename}.canvas"
                
                # Print the full output path for debugging
                print(f"Saving canvas to: {output_file}", file=sys.stderr)
                
                # Create parent directories if they don't exist
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_file, "w") as f:
                    json.dump(canvas.to_dict(), f, indent=2)
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Canvas saved to {output_file}"
                        }
                    ]
                }
            except Exception as e:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error creating canvas: {str(e)}"
                        }
                    ],
                    "isError": True
                }
        
        elif tool_name == "validate_canvas":
            try:
                # Validate the canvas
                canvas_data = args["canvas"]
                
                # Basic validation
                if "nodes" not in canvas_data:
                    raise ValueError("Canvas must have a 'nodes' array")
                
                # Create a canvas from the data to validate it
                canvas = Canvas.from_dict(canvas_data)
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": "Canvas is valid"
                        }
                    ]
                }
            except Exception as e:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Canvas validation failed: {str(e)}"
                        }
                    ],
                    "isError": True
                }
        
        else:
            raise JSONRPCError(
                code=404,
                message=f"Unknown tool: {tool_name}"
            )


if __name__ == "__main__":
    import asyncio
    import uvicorn
    from fastapi import FastAPI
    from mcp.server.fastmcp import FastMCP
    
    # Create a FastAPI app
    app = FastAPI(title="JSON Canvas MCP Server")
    
    # Create the server
    server = JSONCanvasServer()
    
    # Create a FastMCP instance
    fastmcp = FastMCP(server.server)
    
    # Mount the FastMCP app to the FastAPI app
    app.mount("/mcp", fastmcp)
    
    # Add a simple root endpoint
    @app.get("/")
    async def root():
        return {"message": "JSON Canvas MCP Server is running"}
    
    # Run the server
    print("Starting JSON Canvas MCP Server on http://localhost:3000", file=sys.stderr)
    uvicorn.run(app, host="0.0.0.0", port=3000)
