import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
let initialized = false;
let diagramCounter = 0;
const renderDiagram = (el) => {
  mermaid.render(`mermaid-diagram-${diagramCounter++}`, el.textContent || "").then(({ svg, bindFunctions }) => {
    el.innerHTML = svg;
    bindFunctions?.(el);
  }).catch((error) => {
    console.error("Error rendering Mermaid diagram:", error);
    el.setAttribute("data-mermaid-error", "true");
    el.innerHTML = `<p style="color:#666;font-style:italic;">Error rendering diagram</p>`;
  });
};
const processContent = (el) => {
  if (el.querySelector("svg") || el.hasAttribute("data-mermaid-error")) return;
  if (!initialized) {
    mermaid.initialize({
      startOnLoad: false,
      theme: "base",
      securityLevel: "loose",
      flowchart: { useMaxWidth: true, htmlLabels: true, curve: "basis" }
    });
    initialized = true;
  }
  if (el.clientWidth === 0) {
    requestAnimationFrame(() => processContent(el));
    return;
  }
  renderDiagram(el);
};
const mermaidPlugin = {
  name: "mermaid",
  apply({ el }) {
    processContent(el);
    const observer = new MutationObserver(() => {
      observer.disconnect();
      processContent(el);
      observer.observe(el, { childList: true, characterData: true, subtree: true });
    });
    observer.observe(el, { childList: true, characterData: true, subtree: true });
  }
};
var mermaid_default = mermaidPlugin;
export {
  mermaid_default as default
};
