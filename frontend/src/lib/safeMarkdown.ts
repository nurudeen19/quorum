/**
 * Render Markdown to sanitized HTML for display (no raw HTML from source by default).
 */

import DOMPurify from "dompurify";
import MarkdownIt from "markdown-it";

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
  typographer: true,
});

let hooksInstalled = false;

function ensureLinkHook(): void {
  if (hooksInstalled) return;
  hooksInstalled = true;
  DOMPurify.addHook("afterSanitizeAttributes", (node) => {
    if (node.tagName === "A" && node instanceof HTMLAnchorElement) {
      const href = node.getAttribute("href");
      if (href && /^https?:\/\//i.test(href)) {
        node.setAttribute("target", "_blank");
        node.setAttribute("rel", "noopener noreferrer");
      }
    }
  });
}

/**
 * Turn Markdown into HTML safe for ``v-html`` (XSS-resistant).
 */
export function renderSafeMarkdown(source: string): string {
  ensureLinkHook();
  const html = md.render(source || "");
  return DOMPurify.sanitize(html, { USE_PROFILES: { html: true } });
}
