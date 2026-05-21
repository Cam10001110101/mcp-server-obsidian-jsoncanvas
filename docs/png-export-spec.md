# Specification: PNG export

Status: **proposed** (not yet implemented). Tracks adding a `png` format to the existing
`export_canvas` tool.

## Motivation

`export_canvas` already produces `markdown` and `svg` (`jsoncanvas/export.py`). SVG is portable and
dependency-free, but some consumers (chat transcripts, issue trackers, slides, thumbnails) want a
raster image they can drop in directly. The original pre-rewrite README advertised `png` export; it
never worked. This spec defines how to add it cleanly without burdening the core install.

## Tool surface

Extend the existing tool rather than adding a new one:

```
export_canvas(
  filename: str,
  format: Literal["markdown", "svg", "png"],
  scale: float = 2.0,   # png only; raster multiplier, clamped 1.0–3.0
) -> ExportResult
```

- For `png`, `ExportResult.mime_type = "image/png"`. Because base64 in `structuredContent` is
  bulky, the tool ALSO returns an MCP image content block so UI hosts render it inline, and writes
  the file to disk for persistence (see "Return shape").

## Approach: rasterize the existing SVG

Reuse `jsoncanvas/export.py:to_svg(canvas)` — never build a second renderer — then convert
SVG → PNG. Our SVG is intentionally simple (rects, bezier `path`s, arrow `marker`s, `text`), so any
competent SVG rasterizer covers it.

### Rasterizer choice

1. **`resvg` (recommended)** — Rust SVG renderer with prebuilt pip wheels, no system libraries, good
   text shaping. Bundle a sans-serif TTF (e.g. `DejaVuSans.ttf`) under `jsoncanvas/_assets/` and
   register it with resvg's font database so text renders deterministically regardless of host
   fonts.
2. `cairosvg` — needs a system Cairo install; avoid for portability.
3. **Headless Chromium (Playwright)** — highest fidelity (could screenshot the *live viewer* with
   real rendered Markdown, not just title lines), but adds hundreds of MB. Reserve as a future
   opt-in "high-fidelity" mode, not the default.

### Optional dependency

Keep the core install dependency-free. Add an extra in `pyproject.toml`:

```toml
[project.optional-dependencies]
png = ["resvg-py>=…"]   # plus the bundled font as package data
```

`export_canvas(format="png")` imports the rasterizer lazily and, if missing, raises a clear,
actionable error — mirroring the `_load_ui_html()` pattern in `jsoncanvas/server.py`:

> `PNG export requires the optional 'png' extra: pip install "mcp-server-jsoncanvas[png]"`

### Return shape

- Write `<stem>.png` next to the canvas in `OUTPUT_PATH` (reuse `_safe_target`, swapping the
  extension) for persistence.
- Return an MCP **image content block** (`mcp.server.fastmcp.Image` or a raw `ImageContent` with
  base64 + `image/png`) so UI hosts display the render inline.
- Populate `ExportResult` with `{ format: "png", mime_type: "image/png", content: <path or "" > }`
  for text-only hosts (path, not base64, to keep structured output small).

### Sizing

- Render at the SVG's intrinsic pixel size multiplied by `scale`.
- Clamp `scale` to 1.0–3.0 and cap any output dimension at ~4096px to avoid pathological sizes.

## Tests

- `tests/test_export.py`: gate with `pytest.importorskip("resvg_py")` so the suite stays green
  without the extra. Assert the PNG magic bytes (`b"\x89PNG\r\n\x1a\n"`) and plausible
  width/height; assert `scale` changes dimensions; assert the `<stem>.png` file is written.
- `tests/test_server.py`: assert `export_canvas(format="png")` raises the helpful error when the
  extra is absent (or is skipped when present).

## Risks / open questions

- **Fonts:** text needs a registered font; bundling one TTF keeps output deterministic but adds
  ~0.5MB of package data (gated behind the extra).
- **Large canvases:** big boards × `scale` → large PNGs; mitigated by the dimension cap.
- **Fidelity gap:** PNG (like SVG) shows node *title lines* only, not full Markdown. The
  headless-Chromium mode is the path to full fidelity if it's ever needed.
- **resvg feature coverage:** verified sufficient for our SVG subset; revisit if `to_svg` later
  emits gradients, filters, or `foreignObject`.
