"""Error handling for JSON Canvas."""

from enum import IntEnum
from typing import Any, Optional


class ErrorCode(IntEnum):
    """Standard JSON-RPC error codes and custom error codes."""
    # Standard JSON-RPC error codes
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    # Custom error codes for JSON Canvas
    INVALID_NODE = -32000
    INVALID_EDGE = -32001
    VALIDATION_ERROR = -32002
    DUPLICATE_ID = -32003
    REFERENCE_ERROR = -32004


class McpError(Exception):
    """Base class for MCP errors."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        data: Optional[Any] = None
    ) -> None:
        """Initialize MCP error.

        Args:
            code: Error code from ErrorCode enum
            message: Human-readable error message
            data: Optional additional error data
        """
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data

    def to_dict(self) -> dict:
        """Convert error to dictionary format.

        Returns:
            Dictionary representation of the error
        """
        error_dict = {
            "code": self.code,
            "message": self.message
        }
        if self.data is not None:
            error_dict["data"] = self.data
        return error_dict


class ValidationError(McpError):
    """Error raised when validation fails."""

    def __init__(self, message: str, data: Optional[Any] = None) -> None:
        """Initialize validation error.

        Args:
            message: Human-readable error message
            data: Optional validation error details
        """
        super().__init__(ErrorCode.VALIDATION_ERROR, message, data)


class InvalidNodeError(McpError):
    """Error raised when a node is invalid."""

    def __init__(self, message: str, data: Optional[Any] = None) -> None:
        """Initialize invalid node error.

        Args:
            message: Human-readable error message
            data: Optional node error details
        """
        super().__init__(ErrorCode.INVALID_NODE, message, data)


class InvalidEdgeError(McpError):
    """Error raised when an edge is invalid."""

    def __init__(self, message: str, data: Optional[Any] = None) -> None:
        """Initialize invalid edge error.

        Args:
            message: Human-readable error message
            data: Optional edge error details
        """
        super().__init__(ErrorCode.INVALID_EDGE, message, data)


class DuplicateIdError(McpError):
    """Error raised when a duplicate ID is found."""

    def __init__(self, message: str, data: Optional[Any] = None) -> None:
        """Initialize duplicate ID error.

        Args:
            message: Human-readable error message
            data: Optional duplicate ID details
        """
        super().__init__(ErrorCode.DUPLICATE_ID, message, data)


class ReferenceError(McpError):
    """Error raised when a reference is invalid."""

    def __init__(self, message: str, data: Optional[Any] = None) -> None:
        """Initialize reference error.

        Args:
            message: Human-readable error message
            data: Optional reference error details
        """
        super().__init__(ErrorCode.REFERENCE_ERROR, message, data)
