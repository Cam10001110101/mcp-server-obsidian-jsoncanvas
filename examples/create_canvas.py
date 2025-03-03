#!/usr/bin/env python3
"""Example script demonstrating how to use the JSON Canvas library."""

import json
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the jsoncanvas package
sys.path.insert(0, str(Path(__file__).parent.parent))

from jsoncanvas import (
    Canvas,
    TextNode,
    FileNode,
    LinkNode,
    GroupNode,
    Edge,
)


def load_config() -> dict:
    """Load configuration from config.json.

    Returns:
        Dictionary containing configuration values

    Raises:
        FileNotFoundError: If config.json doesn't exist
        KeyError: If required configuration values are missing
    """
    config_path = Path("config.json")
    if not config_path.exists():
        print("Error: config.json not found.")
        print("Please copy config.json.template to config.json and customize it.")
        sys.exit(1)

    with open(config_path) as f:
        config = json.load(f)

    # Validate required configuration
    if "output" not in config:
        raise KeyError("Missing 'output' section in config.json")
    if "path" not in config["output"]:
        raise KeyError("Missing 'path' in output section of config.json")

    return config


def main():
    """Create a sample canvas and save it to a JSON file."""
    # Load configuration
    config = load_config()
    output_path = Path(config["output"]["path"])

    # Create nodes
    title_node = TextNode(
        id="title",
        x=100,
        y=100,
        width=400,
        height=100,
        text="# JSON Canvas Example\n\nThis is a demonstration of the JSON Canvas format.",
        color="#4285F4"  # Google Blue
    )

    file_node = FileNode(
        id="spec",
        x=600,
        y=100,
        width=300,
        height=100,
        file="specification.md",
        subpath="#nodes",
        color="2"  # Orange preset
    )

    link_node = LinkNode(
        id="website",
        x=100,
        y=300,
        width=300,
        height=80,
        url="https://jsoncanvas.org",
        color="4"  # Green preset
    )

    group_node = GroupNode(
        id="examples",
        x=500,
        y=250,
        width=400,
        height=200,
        label="Example Group",
        color="6"  # Purple preset
    )

    code_node = TextNode(
        id="code",
        x=550,
        y=300,
        width=300,
        height=100,
        text="```python\nprint('Hello, JSON Canvas!')\n```"
    )

    # Create edges
    title_to_spec = Edge(
        id="edge1",
        from_node="title",
        to_node="spec",
        from_side="right",
        to_side="left",
        color="1"  # Red preset
    )

    title_to_website = Edge(
        id="edge2",
        from_node="title",
        to_node="website",
        from_side="bottom",
        to_side="top",
        label="Learn More"
    )

    website_to_group = Edge(
        id="edge3",
        from_node="website",
        to_node="examples",
        from_side="right",
        to_side="left"
    )

    # Create canvas and add nodes and edges
    canvas = Canvas()

    # Add nodes (order determines z-index)
    canvas.add_node(group_node)  # Add group first so it's in the background
    canvas.add_node(title_node)
    canvas.add_node(file_node)
    canvas.add_node(link_node)
    canvas.add_node(code_node)

    # Add edges
    canvas.add_edge(title_to_spec)
    canvas.add_edge(title_to_website)
    canvas.add_edge(website_to_group)

    # Convert to dictionary and save as JSON
    canvas_dict = canvas.to_dict()

    # Create the output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)

    # Save to a JSON file
    output_file = output_path / "example.canvas"
    with open(output_file, "w") as f:
        json.dump(canvas_dict, f, indent=2)

    print(f"Canvas saved to {output_file}")

    # Print the JSON to the console
    print("\nCanvas JSON:")
    print(json.dumps(canvas_dict, indent=2))

    # Demonstrate loading from dictionary
    loaded_canvas = Canvas.from_dict(canvas_dict)
    print("\nSuccessfully loaded canvas from dictionary")
    print(f"Number of nodes: {len(loaded_canvas.nodes)}")
    print(f"Number of edges: {len(loaded_canvas.edges)}")


if __name__ == "__main__":
    main()
