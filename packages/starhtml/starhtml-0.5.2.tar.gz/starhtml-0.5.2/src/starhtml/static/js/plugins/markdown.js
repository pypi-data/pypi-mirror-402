import { marked } from "https://cdn.jsdelivr.net/npm/marked/lib/marked.esm.js";
const processContent = (el) => {
  if (el.querySelector("p, h1, h2, h3, ul, ol, blockquote")) return;
  el.innerHTML = marked.parse(el.textContent || "");
};
const markdownPlugin = {
  name: "markdown",
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
var markdown_default = markdownPlugin;
export {
  markdown_default as default
};
