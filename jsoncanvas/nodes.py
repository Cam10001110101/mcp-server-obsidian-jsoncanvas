"""Node implementations for JSON Canvas."""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Union, Literal

from .errors import InvalidNodeError


class Node(ABC):
    """Abstract base class for all node types."""

    def __init__(
        self,
        id: str,
        x: int,
        y: int,
        width: int,
        height: int,
        color: Optional[str] = None
    ) -> None:
        """Initialize a node.

        Args:
            id: Unique identifier for the node
            x: X position of the node in pixels
            y: Y position of the node in pixels
            width: Width of the node in pixels
            height: Height of the node in pixels
            color: Optional color of the node (hex format or preset number)
        """
        self.id = id
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.validate_color(color)
        self.color = color

    @property
    @abstractmethod
    def type(self) -> str:
        """Get the type of the node."""
        pass

    def to_dict(self) -> Dict:
        """Convert node to dictionary representation.

        Returns:
            Dictionary representation of the node
        """
        node_dict = {
            "id": self.id,
            "type": self.type,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }
        if self.color is not None:
            node_dict["color"] = self.color
        return node_dict

    @classmethod
    def validate_color(cls, color: Optional[str]) -> None:
        """Validate a color value.

        Args:
            color: Color value to validate (hex format or preset number)

        Raises:
            InvalidNodeError: If the color is invalid
        """
        if color is not None:
            if not (
                (color.startswith("#") and len(color) == 7) or
                color in ["1", "2", "3", "4", "5", "6"]
            ):
                raise InvalidNodeError(
                    "Color must be a hex code (#RRGGBB) or preset number (1-6)"
                )


class TextNode(Node):
    """Text type node implementation."""

    def __init__(
        self,
        id: str,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str,
        color: Optional[str] = None
    ) -> None:
        """Initialize a text node.

        Args:
            id: Unique identifier for the node
            x: X position of the node in pixels
            y: Y position of the node in pixels
            width: Width of the node in pixels
            height: Height of the node in pixels
            text: Text content with Markdown syntax
            color: Optional color of the node
        """
        super().__init__(id, x, y, width, height, color)
        self.text = text

    @property
    def type(self) -> str:
        """Get the type of the node."""
        return "text"

    def to_dict(self) -> Dict:
        """Convert text node to dictionary representation."""
        node_dict = super().to_dict()
        node_dict["text"] = self.text
        return node_dict


class FileNode(Node):
    """File type node implementation."""

    def __init__(
        self,
        id: str,
        x: int,
        y: int,
        width: int,
        height: int,
        file: str,
        subpath: Optional[str] = None,
        color: Optional[str] = None
    ) -> None:
        """Initialize a file node.

        Args:
            id: Unique identifier for the node
            x: X position of the node in pixels
            y: Y position of the node in pixels
            width: Width of the node in pixels
            height: Height of the node in pixels
            file: Path to the file within the system
            subpath: Optional subpath that may link to a heading or block
            color: Optional color of the node
        """
        super().__init__(id, x, y, width, height, color)
        self.file = file
        if subpath is not None and not subpath.startswith("#"):
            raise InvalidNodeError("Subpath must start with '#'")
        self.subpath = subpath

    @property
    def type(self) -> str:
        """Get the type of the node."""
        return "file"

    def to_dict(self) -> Dict:
        """Convert file node to dictionary representation."""
        node_dict = super().to_dict()
        node_dict["file"] = self.file
        if self.subpath is not None:
            node_dict["subpath"] = self.subpath
        return node_dict


class LinkNode(Node):
    """Link type node implementation."""

    def __init__(
        self,
        id: str,
        x: int,
        y: int,
        width: int,
        height: int,
        url: str,
        color: Optional[str] = None
    ) -> None:
        """Initialize a link node.

        Args:
            id: Unique identifier for the node
            x: X position of the node in pixels
            y: Y position of the node in pixels
            width: Width of the node in pixels
            height: Height of the node in pixels
            url: URL to link to
            color: Optional color of the node
        """
        super().__init__(id, x, y, width, height, color)
        self.url = url

    @property
    def type(self) -> str:
        """Get the type of the node."""
        return "link"

    def to_dict(self) -> Dict:
        """Convert link node to dictionary representation."""
        node_dict = super().to_dict()
        node_dict["url"] = self.url
        return node_dict


class GroupNode(Node):
    """Group type node implementation."""

    def __init__(
        self,
        id: str,
        x: int,
        y: int,
        width: int,
        height: int,
        label: Optional[str] = None,
        background: Optional[str] = None,
        background_style: Optional[Literal["cover", "ratio", "repeat"]] = None,
        color: Optional[str] = None
    ) -> None:
        """Initialize a group node.

        Args:
            id: Unique identifier for the node
            x: X position of the node in pixels
            y: Y position of the node in pixels
            width: Width of the node in pixels
            height: Height of the node in pixels
            label: Optional text label for the group
            background: Optional path to the background image
            background_style: Optional rendering style of the background image
            color: Optional color of the node
        """
        super().__init__(id, x, y, width, height, color)
        self.label = label
        self.background = background
        if background_style not in [None, "cover", "ratio", "repeat"]:
            raise InvalidNodeError(
                "Background style must be one of: cover, ratio, repeat"
            )
        self.background_style = background_style

    @property
    def type(self) -> str:
        """Get the type of the node."""
        return "group"

    def to_dict(self) -> Dict:
        """Convert group node to dictionary representation."""
        node_dict = super().to_dict()
        if self.label is not None:
            node_dict["label"] = self.label
        if self.background is not None:
            node_dict["background"] = self.background
        if self.background_style is not None:
            node_dict["backgroundStyle"] = self.background_style
        return node_dict
