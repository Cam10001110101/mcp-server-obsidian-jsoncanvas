"""Edge implementations for JSON Canvas."""

from typing import Dict, Literal, Optional

from .errors import InvalidEdgeError


class Edge:
    """Edge implementation for connecting nodes."""

    def __init__(
        self,
        id: str,
        from_node: str,
        to_node: str,
        from_side: Optional[Literal["top", "right", "bottom", "left"]] = None,
        from_end: Optional[Literal["none", "arrow"]] = None,
        to_side: Optional[Literal["top", "right", "bottom", "left"]] = None,
        to_end: Optional[Literal["none", "arrow"]] = None,
        color: Optional[str] = None,
        label: Optional[str] = None
    ) -> None:
        """Initialize an edge.

        Args:
            id: Unique identifier for the edge
            from_node: Node ID where the connection starts
            to_node: Node ID where the connection ends
            from_side: Optional side where this edge starts
            from_end: Optional shape of the endpoint at the edge start
            to_side: Optional side where this edge ends
            to_end: Optional shape of the endpoint at the edge end
            color: Optional color of the line
            label: Optional text label for the edge
        """
        self.id = id
        self.from_node = from_node
        self.to_node = to_node
        
        # Validate sides
        valid_sides = ["top", "right", "bottom", "left", None]
        if from_side not in valid_sides:
            raise InvalidEdgeError(
                "from_side must be one of: top, right, bottom, left"
            )
        if to_side not in valid_sides:
            raise InvalidEdgeError(
                "to_side must be one of: top, right, bottom, left"
            )
        self.from_side = from_side
        self.to_side = to_side

        # Validate endpoints
        valid_ends = ["none", "arrow", None]
        if from_end not in valid_ends:
            raise InvalidEdgeError(
                "from_end must be one of: none, arrow"
            )
        if to_end not in valid_ends:
            raise InvalidEdgeError(
                "to_end must be one of: none, arrow"
            )
        self.from_end = from_end or "none"  # Default to "none"
        self.to_end = to_end or "arrow"  # Default to "arrow"

        # Validate color
        self.validate_color(color)
        self.color = color
        
        self.label = label

    @classmethod
    def validate_color(cls, color: Optional[str]) -> None:
        """Validate a color value.

        Args:
            color: Color value to validate (hex format or preset number)

        Raises:
            InvalidEdgeError: If the color is invalid
        """
        if color is not None:
            if not (
                (color.startswith("#") and len(color) == 7) or
                color in ["1", "2", "3", "4", "5", "6"]
            ):
                raise InvalidEdgeError(
                    "Color must be a hex code (#RRGGBB) or preset number (1-6)"
                )

    def to_dict(self) -> Dict:
        """Convert edge to dictionary representation.

        Returns:
            Dictionary representation of the edge
        """
        edge_dict = {
            "id": self.id,
            "fromNode": self.from_node,
            "toNode": self.to_node,
            "fromEnd": self.from_end,
            "toEnd": self.to_end
        }
        
        if self.from_side is not None:
            edge_dict["fromSide"] = self.from_side
        if self.to_side is not None:
            edge_dict["toSide"] = self.to_side
        if self.color is not None:
            edge_dict["color"] = self.color
        if self.label is not None:
            edge_dict["label"] = self.label
            
        return edge_dict

    @classmethod
    def from_dict(cls, data: Dict) -> "Edge":
        """Create an edge from a dictionary.

        Args:
            data: Dictionary representation of an edge

        Returns:
            A new Edge instance
        """
        return cls(
            id=data["id"],
            from_node=data["fromNode"],
            to_node=data["toNode"],
            from_side=data.get("fromSide"),
            from_end=data.get("fromEnd"),
            to_side=data.get("toSide"),
            to_end=data.get("toEnd"),
            color=data.get("color"),
            label=data.get("label")
        )
