#!/usr/bin/env python3
"""Simple MCP server example."""

import asyncio
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    ListResourcesRequest,
    ListToolsRequest,
    ReadResourceRequest,
)

class SimpleMcpServer:
    """A simple MCP server implementation."""

    def __init__(self):
        """Initialize the server."""
        self.server = Server(
            {
                "name": "simple-server",
                "version": "0.1.0",
            },
            {
                "capabilities": {
                    "resources": {},
                    "tools": {},
                },
            },
        )
        
        # Set up handlers
        self.setup_handlers()
        
        # Error handling
        self.server.onerror = lambda error: print(f"[MCP Error] {error}")
    
    def setup_handlers(self):
        """Set up request handlers."""
        # Try different methods to register handlers
        
        # Method 1: Direct assignment to request_handlers
        if hasattr(self.server, 'request_handlers'):
            print("Registering handlers using request_handlers attribute")
            self.server.request_handlers[ListResourcesRequest] = self.handle_list_resources
            self.server.request_handlers[ReadResourceRequest] = self.handle_read_resource
            self.server.request_handlers[ListToolsRequest] = self.handle_list_tools
            self.server.request_handlers[CallToolRequest] = self.handle_call_tool
        
        # Method 2: Using on method
        elif hasattr(self.server, 'on'):
            print("Registering handlers using on method")
            self.server.on(ListResourcesRequest, self.handle_list_resources)
            self.server.on(ReadResourceRequest, self.handle_read_resource)
            self.server.on(ListToolsRequest, self.handle_list_tools)
            self.server.on(CallToolRequest, self.handle_call_tool)
        
        # Method 3: Using register_handler method
        elif hasattr(self.server, 'register_handler'):
            print("Registering handlers using register_handler method")
            self.server.register_handler(ListResourcesRequest, self.handle_list_resources)
            self.server.register_handler(ReadResourceRequest, self.handle_read_resource)
            self.server.register_handler(ListToolsRequest, self.handle_list_tools)
            self.server.register_handler(CallToolRequest, self.handle_call_tool)
        
        else:
            print("ERROR: Could not find a way to register handlers!")
    
    async def handle_list_resources(self, request):
        """Handle list resources request."""
        print("Handling list_resources request")
        return {
            "resources": [
                {
                    "uri": "simple://example",
                    "name": "Example Resource",
                    "mimeType": "text/plain",
                    "description": "An example resource",
                },
            ],
        }
    
    async def handle_read_resource(self, request):
        """Handle read resource request."""
        print(f"Handling read_resource request for {request.params.uri}")
        return {
            "contents": [
                {
                    "uri": request.params.uri,
                    "mimeType": "text/plain",
                    "text": "This is an example resource content.",
                }
            ]
        }
    
    async def handle_list_tools(self, request):
        """Handle list tools request."""
        print("Handling list_tools request")
        return {
            "tools": [
                {
                    "name": "echo",
                    "description": "Echo back the input",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Message to echo"
                            }
                        },
                        "required": ["message"]
                    }
                },
            ]
        }
    
    async def handle_call_tool(self, request):
        """Handle call tool request."""
        print(f"Handling call_tool request for {request.params.name}")
        if request.params.name == "echo":
            message = request.params.arguments.get("message", "")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Echo: {message}"
                    }
                ]
            }
        else:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Unknown tool: {request.params.name}"
                    }
                ],
                "isError": True
            }

if __name__ == "__main__":
    print("Starting simple MCP server...")
    server = SimpleMcpServer()
    asyncio.run(stdio_server(server.server))
