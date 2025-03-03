"""Core functionality for JSON Canvas."""

from typing import Dict, List, Optional, Union, cast

from .errors import DuplicateIdError, ReferenceError, ValidationError
from .nodes import Node, TextNode, FileNode, LinkNode, GroupNode
from .edges import Edge


class Canvas:
    """A JSON Canvas representation according to the 1.0 specification."""

    def __init__(
        self,
        nodes: Optional[List[Node]] = None,
        edges: Optional[List[Edge]] = None
    ) -> None:
        """Initialize a new Canvas.

        Args:
            nodes: Optional list of nodes
            edges: Optional list of edges
        """
        self.nodes = nodes or []
        self.edges = edges or []
        self._validate_ids()
        self._validate_edge_references()

    def _validate_ids(self) -> None:
        """Validate that all node and edge IDs are unique.

        Raises:
            DuplicateIdError: If any duplicate IDs are found
        """
        ids = set()
        # Check node IDs
        for node in self.nodes:
            if node.id in ids:
                raise DuplicateIdError(f"Duplicate node ID found: {node.id}")
            ids.add(node.id)
        # Check edge IDs
        for edge in self.edges:
            if edge.id in ids:
                raise DuplicateIdError(f"Duplicate edge ID found: {edge.id}")
            ids.add(edge.id)

    def _validate_edge_references(self) -> None:
        """Validate that all edge references point to existing nodes.

        Raises:
            ReferenceError: If an edge references a non-existent node
        """
        node_ids = {node.id for node in self.nodes}
        for edge in self.edges:
            if edge.from_node not in node_ids:
                raise ReferenceError(
                    f"Edge {edge.id} references non-existent from_node: {edge.from_node}"
                )
            if edge.to_node not in node_ids:
                raise ReferenceError(
                    f"Edge {edge.id} references non-existent to_node: {edge.to_node}"
                )

    def add_node(self, node: Node) -> None:
        """Add a node to the canvas.

        Args:
            node: The node to add

        Raises:
            DuplicateIdError: If a node with the same ID already exists
        """
        # Check for duplicate ID
        if any(n.id == node.id for n in self.nodes):
            raise DuplicateIdError(f"Node with ID {node.id} already exists")
        self.nodes.append(node)

    def add_edge(self, edge: Edge) -> None:
        """Add an edge to the canvas.

        Args:
            edge: The edge to add

        Raises:
            DuplicateIdError: If an edge with the same ID already exists
            ReferenceError: If the edge references non-existent nodes
        """
        # Check for duplicate ID
        if any(e.id == edge.id for e in self.edges):
            raise DuplicateIdError(f"Edge with ID {edge.id} already exists")
        
        # Validate node references
        node_ids = {node.id for node in self.nodes}
        if edge.from_node not in node_ids:
            raise ReferenceError(
                f"Edge references non-existent from_node: {edge.from_node}"
            )
        if edge.to_node not in node_ids:
            raise ReferenceError(
                f"Edge references non-existent to_node: {edge.to_node}"
            )
            
        self.edges.append(edge)

    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by its ID.

        Args:
            node_id: The ID of the node to get

        Returns:
            The node if found, None otherwise
        """
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_edge(self, edge_id: str) -> Optional[Edge]:
        """Get an edge by its ID.

        Args:
            edge_id: The ID of the edge to get

        Returns:
            The edge if found, None otherwise
        """
        for edge in self.edges:
            if edge.id == edge_id:
                return edge
        return None

    def remove_node(self, node_id: str) -> Optional[Node]:
        """Remove a node and all its connected edges.

        Args:
            node_id: The ID of the node to remove

        Returns:
            The removed node if found, None otherwise
        """
        # Find and remove the node
        node_index = None
        for i, node in enumerate(self.nodes):
            if node.id == node_id:
                node_index = i
                break
        
        if node_index is None:
            return None
            
        removed_node = self.nodes.pop(node_index)
        
        # Remove all edges connected to this node
        self.edges = [
            edge for edge in self.edges
            if edge.from_node != node_id and edge.to_node != node_id
        ]
        
        return removed_node

    def remove_edge(self, edge_id: str) -> Optional[Edge]:
        """Remove an edge.

        Args:
            edge_id: The ID of the edge to remove

        Returns:
            The removed edge if found, None otherwise
        """
        edge_index = None
        for i, edge in enumerate(self.edges):
            if edge.id == edge_id:
                edge_index = i
                break
                
        if edge_index is None:
            return None
            
        return self.edges.pop(edge_index)

    def to_dict(self) -> Dict:
        """Convert the canvas to a dictionary.

        Returns:
            Dictionary representation of the canvas
        """
        canvas_dict: Dict[str, list] = {}
        
        if self.nodes:
            canvas_dict["nodes"] = [node.to_dict() for node in self.nodes]
        if self.edges:
            canvas_dict["edges"] = [edge.to_dict() for edge in self.edges]
            
        return canvas_dict

    @classmethod
    def from_dict(cls, data: Dict) -> "Canvas":
        """Create a Canvas from a dictionary.

        Args:
            data: Dictionary representation of a canvas

        Returns:
            A new Canvas instance

        Raises:
            ValidationError: If the dictionary is invalid
        """
        nodes = []
        edges = []

        # Parse nodes
        for node_data in data.get("nodes", []):
            node_type = node_data.get("type")
            if node_type == "text":
                nodes.append(TextNode(
                    id=node_data["id"],
                    x=node_data["x"],
                    y=node_data["y"],
                    width=node_data["width"],
                    height=node_data["height"],
                    text=node_data["text"],
                    color=node_data.get("color")
                ))
            elif node_type == "file":
                nodes.append(FileNode(
                    id=node_data["id"],
                    x=node_data["x"],
                    y=node_data["y"],
                    width=node_data["width"],
                    height=node_data["height"],
                    file=node_data["file"],
                    subpath=node_data.get("subpath"),
                    color=node_data.get("color")
                ))
            elif node_type == "link":
                nodes.append(LinkNode(
                    id=node_data["id"],
                    x=node_data["x"],
                    y=node_data["y"],
                    width=node_data["width"],
                    height=node_data["height"],
                    url=node_data["url"],
                    color=node_data.get("color")
                ))
            elif node_type == "group":
                nodes.append(GroupNode(
                    id=node_data["id"],
                    x=node_data["x"],
                    y=node_data["y"],
                    width=node_data["width"],
                    height=node_data["height"],
                    label=node_data.get("label"),
                    background=node_data.get("background"),
                    background_style=node_data.get("backgroundStyle"),
                    color=node_data.get("color")
                ))
            else:
                raise ValidationError(f"Invalid node type: {node_type}")

        # Parse edges
        for edge_data in data.get("edges", []):
            edges.append(Edge.from_dict(edge_data))

        return cls(nodes=nodes, edges=edges)
