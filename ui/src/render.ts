/**
 * @file Read-only JSON Canvas renderer.
 *
 * Draws nodes as absolutely-positioned cards and edges as SVG bezier paths in a
 * pan/zoom viewport. Pure DOM, no framework. Colours, sides, and arrow ends
 * follow the JSON Canvas 1.0 spec.
 */
import DOMPurify from "dompurify";
import { marked } from "marked";

type Side = "top" | "right" | "bottom" | "left";
type End = "none" | "arrow";

export interface CanvasNode {
  id: string;
  type?: "text" | "file" | "link" | "group";
  x: number;
  y: number;
  width: number;
  height: number;
  color?: string;
  text?: string;
  file?: string;
  subpath?: string;
  url?: string;
  label?: string;
}

export interface CanvasEdge {
  id: string;
  fromNode: string;
  toNode: string;
  fromSide?: Side;
  toSide?: Side;
  fromEnd?: End;
  toEnd?: End;
  color?: string;
  label?: string;
}

export interface CanvasDocument {
  nodes: CanvasNode[];
  edges: CanvasEdge[];
}

export interface RenderOptions {
  /** Called when a link node or in-content link is activated. */
  onOpenLink?: (url: string) => void;
  /** When provided, an Expand/Collapse button is shown that calls this. */
  onToggleFullscreen?: () => void;
  /** Current host display mode, used to label the Expand/Collapse button. */
  displayMode?: string;
}

/** Handle returned by {@link renderCanvas} so callers can resize/inspect it. */
export interface CanvasController {
  /** Re-run fit-to-view (e.g. after the container is resized). */
  refit(): void;
  /** Natural width of the canvas bounding box (with padding), in canvas units. */
  readonly worldWidth: number;
  /** Natural height of the canvas bounding box (with padding), in canvas units. */
  readonly worldHeight: number;
}

const SVG_NS = "http://www.w3.org/2000/svg";

// Cap fit scale so small canvases grow to fill the viewport (instead of only
// ever shrinking) without blowing tiny canvases up to absurd sizes.
const FIT_MAX_SCALE = 1.75;

// JSON Canvas preset colours 1-6 (Obsidian palette). Hex colours pass through.
const PRESET: Record<string, string> = {
  "1": "#fb464c",
  "2": "#e9973f",
  "3": "#e0de71",
  "4": "#44cf6e",
  "5": "#53dfdd",
  "6": "#a882ff",
};

function resolveColor(c: string | undefined, fallback: string): string {
  if (!c) return fallback;
  return PRESET[c] ?? c;
}

// Only http(s) and mailto URLs are safe to assign to an href or hand to the
// host. This blocks javascript:/data:/etc. from canvas-supplied URLs (which are
// attacker/agent-controlled). Returns the URL when safe, otherwise null.
const SAFE_URL_SCHEME = /^(?:https?:|mailto:)/i;
function safeHref(url: string | undefined): string | null {
  if (!url) return null;
  return SAFE_URL_SCHEME.test(url.trim()) ? url : null;
}

marked.use({ breaks: true, gfm: true });

function renderMarkdown(text: string): string {
  const html = marked.parse(text, { async: false }) as string;
  return DOMPurify.sanitize(html);
}

/** Side of `a` that faces `b`, used when an edge omits an explicit side. */
function autoSide(a: CanvasNode, b: CanvasNode): Side {
  const dx = b.x + b.width / 2 - (a.x + a.width / 2);
  const dy = b.y + b.height / 2 - (a.y + a.height / 2);
  if (Math.abs(dx) > Math.abs(dy)) return dx > 0 ? "right" : "left";
  return dy > 0 ? "bottom" : "top";
}

function sideNormal(side: Side): { x: number; y: number } {
  switch (side) {
    case "top":
      return { x: 0, y: -1 };
    case "bottom":
      return { x: 0, y: 1 };
    case "left":
      return { x: -1, y: 0 };
    case "right":
      return { x: 1, y: 0 };
  }
}

/** Anchor point on a node's side, translated to world origin (minX, minY). */
function anchor(n: CanvasNode, side: Side, minX: number, minY: number) {
  const x = n.x - minX;
  const y = n.y - minY;
  const cx = x + n.width / 2;
  const cy = y + n.height / 2;
  switch (side) {
    case "top":
      return { x: cx, y };
    case "bottom":
      return { x: cx, y: y + n.height };
    case "left":
      return { x, y: cy };
    case "right":
      return { x: x + n.width, y: cy };
  }
}

export function renderCanvas(
  root: HTMLElement,
  doc: CanvasDocument,
  options: RenderOptions = {},
): CanvasController {
  const nodes = doc.nodes ?? [];
  const edges = doc.edges ?? [];

  root.replaceChildren();
  root.classList.add("jc-root");

  if (nodes.length === 0) {
    const empty = document.createElement("div");
    empty.className = "jc-empty";
    empty.textContent = "This canvas has no nodes.";
    root.appendChild(empty);
    return { refit() {}, worldWidth: 800, worldHeight: 300 };
  }

  // World bounding box (with padding) across all nodes.
  const pad = 80;
  const minX = Math.min(...nodes.map((n) => n.x)) - pad;
  const minY = Math.min(...nodes.map((n) => n.y)) - pad;
  const maxX = Math.max(...nodes.map((n) => n.x + n.width)) + pad;
  const maxY = Math.max(...nodes.map((n) => n.y + n.height)) + pad;
  const worldW = Math.max(1, maxX - minX);
  const worldH = Math.max(1, maxY - minY);
  const nodeById = new Map(nodes.map((n) => [n.id, n]));

  const viewport = document.createElement("div");
  viewport.className = "jc-viewport";
  const stage = document.createElement("div");
  stage.className = "jc-stage";
  stage.style.width = `${worldW}px`;
  stage.style.height = `${worldH}px`;
  viewport.appendChild(stage);
  root.appendChild(viewport);

  // --- Edges layer (SVG, behind nodes) ---
  const svg = document.createElementNS(SVG_NS, "svg");
  svg.setAttribute("class", "jc-edges");
  svg.setAttribute("width", String(worldW));
  svg.setAttribute("height", String(worldH));
  svg.setAttribute("viewBox", `0 0 ${worldW} ${worldH}`);
  const defs = document.createElementNS(SVG_NS, "defs");
  svg.appendChild(defs);
  stage.appendChild(svg);

  const markerIds = new Set<string>();
  function arrowMarker(color: string): string {
    const id = `arr-${color.replace(/[^a-zA-Z0-9]/g, "")}`;
    if (!markerIds.has(id)) {
      const marker = document.createElementNS(SVG_NS, "marker");
      marker.setAttribute("id", id);
      marker.setAttribute("viewBox", "0 0 10 10");
      marker.setAttribute("refX", "8");
      marker.setAttribute("refY", "5");
      marker.setAttribute("markerWidth", "7");
      marker.setAttribute("markerHeight", "7");
      marker.setAttribute("orient", "auto-start-reverse");
      const path = document.createElementNS(SVG_NS, "path");
      path.setAttribute("d", "M0,0 L10,5 L0,10 z");
      path.setAttribute("fill", color);
      marker.appendChild(path);
      defs.appendChild(marker);
      markerIds.add(id);
    }
    return id;
  }

  // --- Nodes layer (groups first, so they sit behind) ---
  const layer = document.createElement("div");
  layer.className = "jc-nodes";
  stage.appendChild(layer);

  const ordered = [...nodes].sort(
    (a, b) => (a.type === "group" ? 0 : 1) - (b.type === "group" ? 0 : 1),
  );

  for (const n of ordered) {
    const el = document.createElement("div");
    el.className = `jc-node jc-${n.type ?? "text"}`;
    el.style.left = `${n.x - minX}px`;
    el.style.top = `${n.y - minY}px`;
    el.style.width = `${n.width}px`;
    el.style.height = `${n.height}px`;
    const accent = resolveColor(n.color, "");
    if (accent) el.style.setProperty("--accent", accent);

    if (n.type === "group") {
      if (n.label) {
        const label = document.createElement("div");
        label.className = "jc-group-label";
        label.textContent = n.label;
        el.appendChild(label);
      }
    } else if (n.type === "file") {
      const file = document.createElement("div");
      file.className = "jc-file";
      file.textContent = `📄 ${n.file ?? ""}${n.subpath ?? ""}`;
      el.appendChild(file);
    } else if (n.type === "link") {
      const a = document.createElement("a");
      a.className = "jc-link";
      const href = safeHref(n.url);
      a.href = href ?? "#";
      a.textContent = n.url ?? "";
      a.addEventListener("click", (e) => {
        e.preventDefault();
        if (href) options.onOpenLink?.(href);
      });
      el.appendChild(a);
    } else {
      const body = document.createElement("div");
      body.className = "jc-md";
      body.innerHTML = renderMarkdown(n.text ?? "");
      el.appendChild(body);
    }
    layer.appendChild(el);
  }

  // Route in-content links (from markdown) through the host. DOMPurify has
  // already stripped dangerous schemes; safeHref is the belt-and-braces check.
  layer.addEventListener("click", (e) => {
    const target = e.target as HTMLElement;
    const a = target.closest("a");
    const href = safeHref(a?.getAttribute("href") ?? undefined);
    if (href) {
      e.preventDefault();
      options.onOpenLink?.(href);
    }
  });

  // --- Edges ---
  for (const edge of edges) {
    const from = nodeById.get(edge.fromNode);
    const to = nodeById.get(edge.toNode);
    if (!from || !to) continue;

    const fromSide = edge.fromSide ?? autoSide(from, to);
    const toSide = edge.toSide ?? autoSide(to, from);
    const a = anchor(from, fromSide, minX, minY);
    const b = anchor(to, toSide, minX, minY);
    const k = Math.max(40, Math.hypot(b.x - a.x, b.y - a.y) * 0.4);
    const na = sideNormal(fromSide);
    const nb = sideNormal(toSide);
    const c1 = { x: a.x + na.x * k, y: a.y + na.y * k };
    const c2 = { x: b.x + nb.x * k, y: b.y + nb.y * k };
    const color = resolveColor(edge.color, "var(--color-border, #8a8f98)");

    const path = document.createElementNS(SVG_NS, "path");
    path.setAttribute(
      "d",
      `M${a.x},${a.y} C${c1.x},${c1.y} ${c2.x},${c2.y} ${b.x},${b.y}`,
    );
    path.setAttribute("fill", "none");
    path.setAttribute("stroke", color);
    path.setAttribute("stroke-width", "2");
    // Spec defaults: fromEnd "none", toEnd "arrow".
    if ((edge.toEnd ?? "arrow") === "arrow") {
      path.setAttribute("marker-end", `url(#${arrowMarker(color)})`);
    }
    if ((edge.fromEnd ?? "none") === "arrow") {
      path.setAttribute("marker-start", `url(#${arrowMarker(color)})`);
    }
    svg.appendChild(path);

    if (edge.label) {
      const text = document.createElementNS(SVG_NS, "text");
      text.setAttribute("x", String((a.x + b.x) / 2));
      text.setAttribute("y", String((a.y + b.y) / 2));
      text.setAttribute("class", "jc-edge-label");
      text.setAttribute("text-anchor", "middle");
      text.setAttribute("dominant-baseline", "middle");
      text.textContent = edge.label;
      svg.appendChild(text);
    }
  }

  // --- Pan / zoom ---
  let scale = 1;
  let tx = 0;
  let ty = 0;
  let userInteracted = false;

  function apply() {
    stage.style.transform = `translate(${tx}px, ${ty}px) scale(${scale})`;
  }

  function fit() {
    const r = viewport.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return;
    scale = Math.min(FIT_MAX_SCALE, Math.min(r.width / worldW, r.height / worldH)) || 1;
    tx = (r.width - worldW * scale) / 2;
    ty = (r.height - worldH * scale) / 2;
    apply();
  }

  requestAnimationFrame(fit);

  const resizeObserver = new ResizeObserver(() => {
    if (!userInteracted) fit();
  });
  resizeObserver.observe(viewport);

  viewport.addEventListener(
    "wheel",
    (e) => {
      e.preventDefault();
      userInteracted = true;
      const r = viewport.getBoundingClientRect();
      const mx = e.clientX - r.left;
      const my = e.clientY - r.top;
      const next = Math.min(4, Math.max(0.1, scale * Math.exp(-e.deltaY * 0.001)));
      tx = mx - (mx - tx) * (next / scale);
      ty = my - (my - ty) * (next / scale);
      scale = next;
      apply();
    },
    { passive: false },
  );

  let dragging = false;
  let lastX = 0;
  let lastY = 0;
  viewport.addEventListener("pointerdown", (e) => {
    if ((e.target as HTMLElement).closest("a")) return;
    dragging = true;
    userInteracted = true;
    lastX = e.clientX;
    lastY = e.clientY;
    viewport.setPointerCapture(e.pointerId);
    viewport.classList.add("dragging");
  });
  viewport.addEventListener("pointermove", (e) => {
    if (!dragging) return;
    tx += e.clientX - lastX;
    ty += e.clientY - lastY;
    lastX = e.clientX;
    lastY = e.clientY;
    apply();
  });
  const endDrag = () => {
    dragging = false;
    viewport.classList.remove("dragging");
  };
  viewport.addEventListener("pointerup", endDrag);
  viewport.addEventListener("pointercancel", endDrag);

  // --- Controls ---
  const controls = document.createElement("div");
  controls.className = "jc-controls";

  const fitBtn = document.createElement("button");
  fitBtn.type = "button";
  fitBtn.textContent = "Fit";
  fitBtn.addEventListener("click", () => {
    userInteracted = false;
    fit();
  });
  controls.appendChild(fitBtn);

  if (options.onToggleFullscreen) {
    const fsBtn = document.createElement("button");
    fsBtn.type = "button";
    fsBtn.textContent = options.displayMode === "fullscreen" ? "Collapse" : "Expand";
    fsBtn.addEventListener("click", () => options.onToggleFullscreen!());
    controls.appendChild(fsBtn);
  }

  root.appendChild(controls);

  return { refit: fit, worldWidth: worldW, worldHeight: worldH };
}
