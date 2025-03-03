#!/usr/bin/env python3
"""Simple test script for MCP Server."""

from mcp.server import Server
from mcp.types import ListResourcesRequest

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

# Print the server object
print(f"Server: {server}")

# Try different ways to register a handler
print("\nTrying to register a handler:")

async def handle_list_resources(request):
    return {"resources": []}

# Method 1: Using request_handlers attribute
print("Method 1: Using request_handlers attribute")
if hasattr(server, 'request_handlers'):
    print(f"  server.request_handlers: {server.request_handlers}")
    try:
        server.request_handlers[ListResourcesRequest] = handle_list_resources
        print("  Successfully registered handler using request_handlers")
    except Exception as e:
        print(f"  Error: {e}")

# Method 2: Using on method if available
print("\nMethod 2: Using 'on' method if available")
if hasattr(server, 'on'):
    try:
        server.on(ListResourcesRequest, handle_list_resources)
        print("  Successfully registered handler using on method")
    except Exception as e:
        print(f"  Error: {e}")

# Method 3: Using register_handler method if available
print("\nMethod 3: Using 'register_handler' method if available")
if hasattr(server, 'register_handler'):
    try:
        server.register_handler(ListResourcesRequest, handle_list_resources)
        print("  Successfully registered handler using register_handler method")
    except Exception as e:
        print(f"  Error: {e}")

# Print all attributes that might be related to handlers
print("\nAttributes that might be related to handlers:")
for attr in dir(server):
    if 'handler' in attr.lower() or 'request' in attr.lower():
        print(f"  {attr}")
