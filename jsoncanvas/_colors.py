"""Shared colour validation for JSON Canvas nodes and edges.

A JSON Canvas colour is either a 6-digit hex code (``#RRGGBB``) or one of the
preset numbers ``"1"`` through ``"6"`` (the Obsidian palette). Keeping the rule
in one place stops the node and edge validators from drifting, and the strict hex
match prevents non-hex values (e.g. ``#"/><g``) from slipping through into the
SVG export.
"""

import re

_HEX_RE = re.compile(r"#[0-9a-fA-F]{6}")
_PRESETS = frozenset("123456")


def is_valid_color(color: object) -> bool:
    """Return True if ``color`` is a valid JSON Canvas colour value."""
    return isinstance(color, str) and (
        _HEX_RE.fullmatch(color) is not None or color in _PRESETS
    )
