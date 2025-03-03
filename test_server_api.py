#!/usr/bin/env python3
"""Test script to explore the MCP Server API."""

import inspect
from mcp.server import Server

# Create a server instance
server = Server(
    {
        "name": "test-server",
        "version": "0.1.0",
    },
    {
        "capabilities": {
            "resources": {},
            "tools": {},
        },
    },
)

# Print available methods and attributes
print("Server attributes and methods:")
for name, obj in inspect.getmembers(server):
    if not name.startswith('_'):  # Skip private/internal attributes
        if inspect.ismethod(obj):
            print(f"  Method: {name}{inspect.signature(obj)}")
        else:
            print(f"  Attribute: {name} (type: {type(obj).__name__})")

# Print docstring if available
if server.__doc__:
    print("\nServer docstring:")
    print(server.__doc__)
