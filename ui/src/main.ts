/**
 * @file MCP App entry point for the JSON Canvas viewer.
 *
 * Wires the ext-apps {@link App} client to the canvas renderer and owns the
 * viewer's sizing: the host drives the iframe width and the app drives the
 * height. We derive a height from the canvas aspect ratio (filling the width,
 * clamped to a sensible range), set it on the root, and report it via
 * `sendSizeChanged` so the host grows its iframe. An Expand button switches to
 * the host's fullscreen display mode when available.
 */
import {
  App,
  applyDocumentTheme,
  applyHostFonts,
  applyHostStyleVariables,
  type McpUiHostContext,
} from "@modelcontextprotocol/ext-apps";
import {
  renderCanvas,
  type CanvasController,
  type CanvasDocument,
} from "./render";
import "./styles.css";

const rootEl = document.getElementById("root") as HTMLElement;

// Inline sizing: fill the available width (scaling up to FILL_MAX_SCALE), with
// the height following the canvas aspect ratio, clamped so the card is never
// tiny nor page-dominating. Fullscreen uses the host's container height.
const INLINE_MIN_H = 320;
const INLINE_MAX_H = 600;
const FILL_MAX_SCALE = 1.75;

/**
 * Pull the canvas document out of a tool result. `read_canvas` returns the
 * document directly (`{nodes, edges}`); `create_canvas` / `edit_canvas` nest it
 * under `canvas`.
 */
function extractDoc(structuredContent: unknown): CanvasDocument | null {
  const sc = structuredContent as Record<string, unknown> | undefined;
  if (!sc) return null;
  const doc = ("canvas" in sc ? sc.canvas : sc) as CanvasDocument | undefined;
  return doc && Array.isArray(doc.nodes) ? doc : null;
}

const app = new App({ name: "JSON Canvas Viewer", version: "0.1.0" });

let currentDoc: CanvasDocument | null = null;
let controller: CanvasController | null = null;
let displayMode = "inline";
let fullscreenAvailable = false;

const onOpenLink = (url: string) => void app.openLink({ url });

function clamp(value: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, value));
}

function containerWidth(): number {
  const dims = app.getHostContext()?.containerDimensions as
    | { width?: number; maxWidth?: number }
    | undefined;
  return dims?.width ?? dims?.maxWidth ?? document.documentElement.clientWidth ?? 760;
}

/** Size the root to fit the canvas and report the height to the host. */
function layout(): void {
  if (!controller) return;
  if (displayMode === "fullscreen") {
    const dims = app.getHostContext()?.containerDimensions as
      | { height?: number }
      | undefined;
    rootEl.style.height = `${dims?.height ?? window.innerHeight}px`;
    controller.refit();
    return;
  }
  const width = containerWidth();
  const scale = Math.min(FILL_MAX_SCALE, width / controller.worldWidth);
  const height = clamp(
    Math.round(controller.worldHeight * scale),
    INLINE_MIN_H,
    INLINE_MAX_H,
  );
  rootEl.style.height = `${height}px`;
  controller.refit();
  app.sendSizeChanged({ width: Math.round(width), height });
}

async function toggleFullscreen(): Promise<void> {
  const next = displayMode === "fullscreen" ? "inline" : "fullscreen";
  try {
    const result = await app.requestDisplayMode({ mode: next });
    displayMode = result.mode ?? next;
  } catch (err) {
    console.error("[canvas-viewer] requestDisplayMode failed", err);
    displayMode = next;
  }
  if (currentDoc) render(currentDoc);
}

function render(doc: CanvasDocument): void {
  controller = renderCanvas(rootEl, doc, {
    onOpenLink,
    displayMode,
    onToggleFullscreen: fullscreenAvailable ? toggleFullscreen : undefined,
  });
  layout();
}

function applyHostContext(ctx: McpUiHostContext): void {
  if (ctx.theme) applyDocumentTheme(ctx.theme);
  if (ctx.styles?.variables) applyHostStyleVariables(ctx.styles.variables);
  if (ctx.styles?.css?.fonts) applyHostFonts(ctx.styles.css.fonts);
  if (ctx.safeAreaInsets) {
    const { top, right, bottom, left } = ctx.safeAreaInsets;
    document.body.style.padding = `${top}px ${right}px ${bottom}px ${left}px`;
  }

  const prevMode = displayMode;
  if (ctx.displayMode) displayMode = ctx.displayMode;
  if (ctx.availableDisplayModes) {
    fullscreenAvailable = ctx.availableDisplayModes.includes("fullscreen");
  }

  if (!currentDoc) return;
  if (displayMode !== prevMode) {
    render(currentDoc); // re-render to relabel Expand/Collapse + relayout
  } else {
    layout(); // width / container change
  }
}

// Register all handlers BEFORE connecting.
app.onteardown = async () => ({});
app.ontoolinput = () => {};
app.ontoolresult = (result) => {
  const doc = extractDoc(result.structuredContent);
  if (doc) {
    currentDoc = doc;
    render(doc);
  }
};
app.onerror = (err) => console.error("[canvas-viewer]", err);
app.onhostcontextchanged = applyHostContext;

app.connect().then(() => {
  const ctx = app.getHostContext();
  if (ctx) applyHostContext(ctx);
});
