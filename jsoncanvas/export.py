"""Export a :class:`~jsoncanvas.canvas.Canvas` to other formats.

``to_markdown`` produces an edge-ordered outline; ``to_svg`` produces a
standalone vector image. Both are dependency-free and operate on the typed
``Canvas`` model. SVG renders each node's title line only (plain SVG cannot
render Markdown).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .canvas import Canvas
    from .nodes import Node

# JSON Canvas preset colours 1-6 (Obsidian palette); hex colours pass through.
_PRESET = {
    "1": "#fb464c",
    "2": "#e9973f",
    "3": "#e0de71",
    "4": "#44cf6e",
    "5": "#53dfdd",
    "6": "#a882ff",
}
_DEFAULT_STROKE = "#8a8f98"


def _color(value: str | None, fallback: str = _DEFAULT_STROKE) -> str:
    # Resolve presets, then escape: colours are interpolated into SVG attribute
    # values, so this is the backstop layer behind ``is_valid_color`` (the model
    # already rejects non-hex colours, making this a no-op for valid input).
    raw = fallback if not value else _PRESET.get(value, value)
    return _esc(raw)


# --------------------------------------------------------------------------- #
# Markdown
# --------------------------------------------------------------------------- #
def _node_title(node: Node) -> str:
    """A one-line label for a node: first text line, else label/file/url/id."""
    text = getattr(node, "text", None)
    if text:
        for line in text.splitlines():
            stripped = line.strip().lstrip("#").strip()
            if stripped:
                return stripped
    return (
        getattr(node, "label", None)
        or getattr(node, "file", None)
        or getattr(node, "url", None)
        or node.id
    )


def _node_body(node: Node) -> str:
    """The detail block for a node beneath its heading (may be empty)."""
    text = getattr(node, "text", None)
    if text:
        # Everything after the first non-empty (title) line.
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if line.strip():
                return "\n".join(lines[i + 1 :]).strip()
        return ""
    file = getattr(node, "file", None)
    if file:
        subpath = getattr(node, "subpath", None) or ""
        return f"File: `{file}{subpath}`"
    url = getattr(node, "url", None)
    if url:
        return f"<{url}>"
    return ""


def to_markdown(canvas: Canvas, title: str = "Canvas") -> str:
    """Render a canvas as a Markdown document.

    Nodes are ordered by a depth-first walk of the edges starting from roots
    (nodes with no incoming edge), so connected flows read top to bottom; any
    remaining nodes (cycles/disconnected) follow. Edges are listed at the end.
    """
    nodes_by_id = {n.id: n for n in canvas.nodes}
    children: dict[str, list[str]] = {}
    indegree = {n.id: 0 for n in canvas.nodes}
    for edge in canvas.edges:
        children.setdefault(edge.from_node, []).append(edge.to_node)
        if edge.to_node in indegree:
            indegree[edge.to_node] += 1

    roots = [n.id for n in canvas.nodes if indegree.get(n.id, 0) == 0]
    if not roots:  # fully cyclic — fall back to document order
        roots = [n.id for n in canvas.nodes]

    order: list[str] = []
    seen: set[str] = set()

    def visit(start: str) -> None:
        # Iterative pre-order DFS (an explicit stack avoids RecursionError on
        # long edge chains). Children are pushed in reverse so the leftmost is
        # popped first, matching the previous recursive traversal order.
        stack = [start]
        while stack:
            node_id = stack.pop()
            if node_id in seen or node_id not in nodes_by_id:
                continue
            seen.add(node_id)
            order.append(node_id)
            stack.extend(reversed(children.get(node_id, [])))

    for root in roots:
        visit(root)
    for node in canvas.nodes:  # leftovers
        visit(node.id)

    lines = [f"# {title}", ""]
    for node_id in order:
        node = nodes_by_id[node_id]
        lines.append(f"## {_node_title(node)}")
        body = _node_body(node)
        if body:
            lines.append("")
            lines.append(body)
        lines.append("")

    if canvas.edges:
        lines.append("## Connections")
        for edge in canvas.edges:
            frm = (
                _node_title(nodes_by_id[edge.from_node])
                if edge.from_node in nodes_by_id
                else edge.from_node
            )
            to = (
                _node_title(nodes_by_id[edge.to_node])
                if edge.to_node in nodes_by_id
                else edge.to_node
            )
            label = f" — {edge.label}" if edge.label else ""
            lines.append(f"- {frm} → {to}{label}")
        lines.append("")

    return "\n".join(lines).rstrip("\n") + "\n"


# --------------------------------------------------------------------------- #
# SVG
# --------------------------------------------------------------------------- #
_SIDES = ("top", "right", "bottom", "left")


def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _auto_side(a: Node, b: Node) -> str:
    """Side of ``a`` facing ``b`` (used when an edge omits a side)."""
    dx = (b.x + b.width / 2) - (a.x + a.width / 2)
    dy = (b.y + b.height / 2) - (a.y + a.height / 2)
    if abs(dx) > abs(dy):
        return "right" if dx > 0 else "left"
    return "bottom" if dy > 0 else "top"


def _normal(side: str) -> tuple[float, float]:
    return {
        "top": (0.0, -1.0),
        "bottom": (0.0, 1.0),
        "left": (-1.0, 0.0),
        "right": (1.0, 0.0),
    }[side]


def _anchor(node: Node, side: str, min_x: int, min_y: int) -> tuple[float, float]:
    x = node.x - min_x
    y = node.y - min_y
    cx = x + node.width / 2
    cy = y + node.height / 2
    if side == "top":
        return cx, y
    if side == "bottom":
        return cx, y + node.height
    if side == "left":
        return x, cy
    return x + node.width, cy


def _wrap(title: str, width: int, height: int) -> list[str]:
    """Greedy word-wrap of a title to fit a node box (rough px estimate)."""
    char_w = 7.5  # ~13px sans-serif
    max_chars = max(4, int((width - 16) / char_w))
    max_lines = max(1, int((height - 12) / 18))
    words = title.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
        if len(lines) >= max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    if not lines:
        lines = [title[:max_chars]]
    # Truncate the last line if the title overflowed the available lines.
    consumed = sum(len(line.split()) for line in lines)
    if consumed < len(words) and lines:
        last = lines[-1]
        if len(last) >= max_chars - 1:
            lines[-1] = last[: max_chars - 1] + "…"
        else:
            lines[-1] = last + " …"
    return lines


def to_svg(canvas: Canvas) -> str:
    """Render a canvas as a standalone SVG string (light theme, titles only)."""
    if not canvas.nodes:
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" width="320" height="120">'
            '<text x="20" y="60" font-family="sans-serif" font-size="14" '
            'fill="#666">Empty canvas</text></svg>'
        )

    pad = 40
    min_x = min(n.x for n in canvas.nodes) - pad
    min_y = min(n.y for n in canvas.nodes) - pad
    max_x = max(n.x + n.width for n in canvas.nodes) + pad
    max_y = max(n.y + n.height for n in canvas.nodes) + pad
    w = max(1, max_x - min_x)
    h = max(1, max_y - min_y)
    nodes_by_id = {n.id: n for n in canvas.nodes}

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="-apple-system, system-ui, sans-serif">'
    ]
    parts.append(f'<rect width="{w}" height="{h}" fill="#ffffff"/>')

    # Arrow markers, one per distinct edge colour.
    marker_ids: dict[str, str] = {}
    marker_defs: list[str] = []
    for edge in canvas.edges:
        col = _color(getattr(edge, "color", None))
        if col not in marker_ids:
            mid = f"arrow{len(marker_ids)}"
            marker_ids[col] = mid
            marker_defs.append(
                f'<marker id="{mid}" viewBox="0 0 10 10" refX="8" refY="5" '
                f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
                f'<path d="M0,0 L10,5 L0,10 z" fill="{col}"/></marker>'
            )
    if marker_defs:
        parts.append("<defs>" + "".join(marker_defs) + "</defs>")

    # Edges (drawn under nodes).
    for edge in canvas.edges:
        a = nodes_by_id.get(edge.from_node)
        b = nodes_by_id.get(edge.to_node)
        if a is None or b is None:
            continue
        from_side = getattr(edge, "from_side", None) or _auto_side(a, b)
        to_side = getattr(edge, "to_side", None) or _auto_side(b, a)
        ax, ay = _anchor(a, from_side, min_x, min_y)
        bx, by = _anchor(b, to_side, min_x, min_y)
        k = max(40.0, ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5 * 0.4)
        nax, nay = _normal(from_side)
        nbx, nby = _normal(to_side)
        c1x, c1y = ax + nax * k, ay + nay * k
        c2x, c2y = bx + nbx * k, by + nby * k
        col = _color(getattr(edge, "color", None))
        marker = ""
        if (getattr(edge, "to_end", None) or "arrow") == "arrow":
            marker = f' marker-end="url(#{marker_ids[col]})"'
        start_marker = ""
        if (getattr(edge, "from_end", None) or "none") == "arrow":
            start_marker = f' marker-start="url(#{marker_ids[col]})"'
        parts.append(
            f'<path d="M{ax:.1f},{ay:.1f} C{c1x:.1f},{c1y:.1f} {c2x:.1f},{c2y:.1f} '
            f'{bx:.1f},{by:.1f}" fill="none" stroke="{col}" stroke-width="2"'
            f"{marker}{start_marker}/>"
        )
        if getattr(edge, "label", None):
            lx, ly = (ax + bx) / 2, (ay + by) / 2
            parts.append(
                f'<text x="{lx:.1f}" y="{ly:.1f}" font-size="12" fill="#333" '
                f'text-anchor="middle" paint-order="stroke" stroke="#ffffff" '
                f'stroke-width="3">{_esc(edge.label)}</text>'
            )

    # Nodes (groups first so they sit behind).
    ordered = sorted(canvas.nodes, key=lambda n: 0 if n.type == "group" else 1)
    for node in ordered:
        x = node.x - min_x
        y = node.y - min_y
        stroke = _color(getattr(node, "color", None), "#c8ccd2")
        if node.type == "group":
            parts.append(
                f'<rect x="{x}" y="{y}" width="{node.width}" height="{node.height}" '
                f'rx="10" fill="{stroke}" fill-opacity="0.06" stroke="{stroke}" '
                f'stroke-width="2" stroke-dasharray="6 4"/>'
            )
            label = getattr(node, "label", None)
            if label:
                parts.append(
                    f'<text x="{x + 10}" y="{y + 20}" font-size="13" '
                    f'font-weight="600" fill="#333">{_esc(label)}</text>'
                )
            continue
        parts.append(
            f'<rect x="{x}" y="{y}" width="{node.width}" height="{node.height}" '
            f'rx="8" fill="#ffffff" stroke="{stroke}" stroke-width="2"/>'
        )
        title_lines = _wrap(_node_title(node), node.width, node.height)
        for i, line in enumerate(title_lines):
            parts.append(
                f'<text x="{x + 10}" y="{y + 24 + i * 18}" font-size="13" '
                f'fill="#1a1a1a">{_esc(line)}</text>'
            )

    parts.append("</svg>")
    return "".join(parts)
