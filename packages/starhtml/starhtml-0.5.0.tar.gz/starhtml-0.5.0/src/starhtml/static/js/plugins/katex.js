import katex from "https://cdn.jsdelivr.net/npm/katex/dist/katex.mjs";
import { marked } from "https://cdn.jsdelivr.net/npm/marked/lib/marked.esm.js";
const renderMath = (tex, displayMode) => katex.renderToString(tex, { throwOnError: false, displayMode, output: "html", trust: true });
const processContent = (el) => {
  if (el.querySelector(".katex")) return;
  let content = el.textContent || "";
  content = content.replace(/\\\[([\s\S]+?)\\\]/gm, (_, tex) => renderMath(tex.trim(), true));
  content = content.replace(/\$\$([\s\S]+?)\$\$/gm, (_, tex) => renderMath(tex.trim(), true));
  content = content.replace(/\\\(([\s\S]+?)\\\)/g, (_, tex) => renderMath(tex.trim(), false));
  content = content.replace(
    /(?<!\w)\$([^\$\s](?:[^\$]*[^\$\s])?)\$(?!\w)/g,
    (_, tex) => renderMath(tex.trim(), false)
  );
  el.innerHTML = marked.parse(content);
};
const katexPlugin = {
  name: "katex",
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
var katex_default = katexPlugin;
export {
  katex_default as default
};
