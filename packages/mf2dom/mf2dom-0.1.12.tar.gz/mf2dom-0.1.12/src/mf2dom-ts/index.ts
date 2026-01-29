/**
 * mf2dom-ts - TypeScript Microformats2 Renderer
 *
 * Efficiently renders mf2json to semantic HTML using modern DOM APIs.
 *
 * @example
 * ```typescript
 * import { render, renderItemElement, registerElements } from 'mf2dom-ts';
 *
 * // Render document to HTML string
 * const html = render(mf2Document);
 *
 * // Render directly to DOM element
 * const main = render(mf2Document, { asElement: true });
 * document.body.appendChild(main);
 *
 * // Use custom elements
 * registerElements();
 * const el = document.createElement('mf2-item');
 * el.item = { type: ['h-card'], properties: { name: ['Alice'] } };
 * ```
 */

// Core types
export type {
  Mf2Document,
  Mf2Item,
  PropertyValue,
  EValue,
  UrlObject,
  RelUrl,
} from "./types.js";

// Core renderer
export { render, renderItemElement, parseHtmlFragment } from "./renderer.js";

// Web Components
export {
  Mf2ItemElement,
  Mf2DocumentElement,
  Mf2FeedElement,
  registerElements,
  type FeedOptions,
} from "./components.js";
