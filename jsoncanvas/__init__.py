"""JSON Canvas package."""

from .canvas import Canvas
from .edges import Edge
from .errors import (
    DuplicateIdError,
    InvalidEdgeError,
    InvalidNodeError,
    McpError,
    ReferenceError,
    ValidationError,
)
from .nodes import FileNode, GroupNode, LinkNode, Node, TextNode

__version__ = "0.2.0"

__all__ = [
    "__version__",
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
