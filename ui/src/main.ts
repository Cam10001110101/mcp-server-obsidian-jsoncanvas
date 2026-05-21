/**
 * @file MCP App entry point for the JSON Canvas viewer.
 *
 * Wires the ext-apps {@link App} client to the canvas renderer. The server's
 * `read_canvas` / `create_canvas` tools carry `_meta.ui.resourceUri` pointing at
 * this bundle and return the canvas in `structuredContent`, which arrives here
 * via the `ontoolresult` handler.
 */
import {
  App,
  applyDocumentTheme,
  applyHostFonts,
  applyHostStyleVariables,
  type McpUiHostContext,
} from "@modelcontextprotocol/ext-apps";
import { renderCanvas, type CanvasDocument } from "./render";
import "./styles.css";

const rootEl = document.getElementById("root") as HTMLElement;

/**
 * Pull the canvas document out of a tool result. `read_canvas` returns the
 * document directly (`{nodes, edges}`); `create_canvas` nests it under `canvas`.
 */
function extractDoc(structuredContent: unknown): CanvasDocument | null {
  const sc = structuredContent as Record<string, unknown> | undefined;
  if (!sc) return null;
  const doc = ("canvas" in sc ? sc.canvas : sc) as CanvasDocument | undefined;
  return doc && Array.isArray(doc.nodes) ? doc : null;
}

const app = new App({ name: "JSON Canvas Viewer", version: "0.1.0" });

function applyHostContext(ctx: McpUiHostContext) {
  if (ctx.theme) applyDocumentTheme(ctx.theme);
  if (ctx.styles?.variables) applyHostStyleVariables(ctx.styles.variables);
  if (ctx.styles?.css?.fonts) applyHostFonts(ctx.styles.css.fonts);
  if (ctx.safeAreaInsets) {
    const { top, right, bottom, left } = ctx.safeAreaInsets;
    document.body.style.padding = `${top}px ${right}px ${bottom}px ${left}px`;
  }
}

const onOpenLink = (url: string) => {
  void app.openLink({ url });
};

// Register all handlers BEFORE connecting.
app.onteardown = async () => ({});
app.ontoolinput = () => {};
app.ontoolresult = (result) => {
  const doc = extractDoc(result.structuredContent);
  if (doc) renderCanvas(rootEl, doc, { onOpenLink });
};
app.onerror = (err) => console.error("[canvas-viewer]", err);
app.onhostcontextchanged = applyHostContext;

app.connect().then(() => {
  const ctx = app.getHostContext();
  if (ctx) applyHostContext(ctx);
});
