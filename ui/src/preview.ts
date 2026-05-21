/**
 * @file Standalone dev preview — renders a sample canvas without an MCP host.
 * Not included in the production build (only `viewer.html` is). Use via
 * `npm run dev` → open /preview.html.
 */
import { renderCanvas, type CanvasDocument } from "./render";
import "./styles.css";

const sample: CanvasDocument = {
  nodes: [
    { id: "events_group", type: "group", x: 150, y: 450, width: 1000, height: 250, color: "#EA4335", label: "Events & Activities" },
    { id: "resources_group", type: "group", x: 150, y: 750, width: 1000, height: 200, color: "#673AB7", label: "Resources" },
    { id: "title", type: "text", text: "# Austin LangChain AI Meetup Group\n\nA community for AI enthusiasts and developers in Austin, TX", x: 400, y: -80, width: 500, height: 160, color: "#4285F4" },
    { id: "about", type: "text", text: "## About the Group\n\nThe Austin LangChain AI Meetup Group brings together developers, researchers, and enthusiasts interested in LangChain, LLMs, and AI application development.", x: 150, y: 120, width: 350, height: 280, color: "#34A853" },
    { id: "langchain", type: "text", text: "## What is LangChain?\n\nLangChain is a framework for developing applications powered by language models. It enables:\n\n- Connecting LLMs to data\n- Creating interactive agents\n- Building context-aware apps", x: 800, y: 200, width: 350, height: 200, color: "#FBBC05" },
    { id: "workshops", type: "text", text: "## Workshops\n\n- Hands-on LangChain tutorials\n- Building AI applications\n- RAG implementation techniques", x: 200, y: 500, width: 250, height: 150, color: "1" },
    { id: "talks", type: "text", text: "## Speaker Series\n\n- Industry experts\n- Academic researchers\n- Open source contributors", x: 500, y: 500, width: 250, height: 150, color: "4" },
    { id: "hackathons", type: "text", text: "## Hackathons\n\n- Weekend coding events\n- Team-based challenges\n- Prizes and recognition", x: 800, y: 500, width: 250, height: 150, color: "3" },
    { id: "github", type: "link", url: "https://github.com/langchain-ai/langchain", x: 500, y: 800, width: 250, height: 100, color: "#333333" },
    { id: "join", type: "text", text: "## Join the Community\n\nConnect with AI enthusiasts and LangChain developers in Austin! Our meetups are open to all skill levels.", x: 400, y: 1000, width: 500, height: 220, color: "#FF5722" },
  ],
  edges: [
    { id: "edge1", fromNode: "title", fromSide: "bottom", toNode: "about", toSide: "top" },
    { id: "edge2", fromNode: "title", fromSide: "bottom", toNode: "langchain", toSide: "top" },
    { id: "edge3", fromNode: "about", fromSide: "bottom", toNode: "events_group", toSide: "top" },
    { id: "edge4", fromNode: "langchain", fromSide: "bottom", toNode: "events_group", toSide: "top" },
    { id: "edge5", fromNode: "events_group", fromSide: "bottom", toNode: "resources_group", toSide: "top" },
    { id: "edge6", fromNode: "resources_group", fromSide: "bottom", toNode: "join", toSide: "top" },
    { id: "edge7", fromNode: "langchain", fromSide: "bottom", toNode: "github", toSide: "top", label: "Source Code" },
  ],
};

// No MCP host here to drive the iframe height, so fill the page directly.
const previewRoot = document.getElementById("root") as HTMLElement;
previewRoot.style.height = "100vh";
renderCanvas(previewRoot, sample, {
  onOpenLink: (url) => window.open(url, "_blank"),
});
