"""JSON Canvas package."""

from .canvas import Canvas
from .nodes import Node, TextNode, FileNode, LinkNode, GroupNode
from .edges import Edge
from .errors import (
    McpError,
    ValidationError,
    InvalidNodeError,
    InvalidEdgeError,
    DuplicateIdError,
    ReferenceError,
)

__version__ = "0.1.0"

__all__ = [
    "Canvas",
    "Node",
    "TextNode",
    "FileNode",
    "LinkNode",
    "GroupNode",
    "Edge",
    "McpError",
    "ValidationError",
    "InvalidNodeError",
    "InvalidEdgeError",
    "DuplicateIdError",
    "ReferenceError",
]
