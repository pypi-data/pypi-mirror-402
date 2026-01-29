/**
 * Web Components for mf2 rendering
 *
 * Custom Elements that render mf2json data efficiently in the browser.
 * Perfect for use with sql-wasm.js and client-side databases.
 */

import type { Mf2Item, Mf2Document, RelUrl } from "./types.js";
import { render, renderItemElement } from "./renderer.js";

// ============================================================================
// <mf2-item> - Renders a single mf2 item
// ============================================================================

/**
 * Custom element that renders a single mf2 item.
 *
 * Usage:
 * ```html
 * <mf2-item></mf2-item>
 * <script>
 *   const el = document.querySelector('mf2-item');
 *   el.item = { type: ['h-card'], properties: { name: ['Alice'] } };
 * </script>
 * ```
 *
 * Or with JSON attribute:
 * ```html
 * <mf2-item data-json='{"type":["h-card"],"properties":{"name":["Alice"]}}'></mf2-item>
 * ```
 */
export class Mf2ItemElement extends HTMLElement {
  static observedAttributes = ["data-json"];

  #item: Mf2Item | null = null;
  #relUrls: Record<string, RelUrl> | undefined;
  #rendered = false;

  constructor() {
    super();
  }

  /** The mf2 item to render */
  get item(): Mf2Item | null {
    return this.#item;
  }

  set item(value: Mf2Item | null) {
    this.#item = value;
    this.#render();
  }

  /** Optional rel-urls for link relations */
  get relUrls(): Record<string, RelUrl> | undefined {
    return this.#relUrls;
  }

  set relUrls(value: Record<string, RelUrl> | undefined) {
    this.#relUrls = value;
    if (this.#item) this.#render();
  }

  connectedCallback() {
    if (!this.#rendered) {
      this.#render();
    }
  }

  attributeChangedCallback(name: string, _oldValue: string, newValue: string) {
    if (name === "data-json" && newValue) {
      try {
        this.#item = JSON.parse(newValue);
        this.#render();
      } catch (e) {
        console.error("Invalid JSON in data-json attribute:", e);
      }
    }
  }

  #render() {
    if (!this.isConnected) return;

    // Clear existing content
    this.innerHTML = "";

    if (!this.#item) return;

    const element = renderItemElement(this.#item, this.#relUrls);
    this.appendChild(element);
    this.#rendered = true;
  }
}

// ============================================================================
// <mf2-document> - Renders a full mf2 document
// ============================================================================

/**
 * Custom element that renders an entire mf2 document.
 *
 * Usage:
 * ```html
 * <mf2-document></mf2-document>
 * <script>
 *   const el = document.querySelector('mf2-document');
 *   el.document = { items: [...], rels: {}, 'rel-urls': {} };
 * </script>
 * ```
 */
export class Mf2DocumentElement extends HTMLElement {
  static observedAttributes = ["data-json"];

  #document: Mf2Document | null = null;
  #rendered = false;

  constructor() {
    super();
  }

  get document(): Mf2Document | null {
    return this.#document;
  }

  set document(value: Mf2Document | null) {
    this.#document = value;
    this.#render();
  }

  connectedCallback() {
    if (!this.#rendered) {
      this.#render();
    }
  }

  attributeChangedCallback(name: string, _oldValue: string, newValue: string) {
    if (name === "data-json" && newValue) {
      try {
        this.#document = JSON.parse(newValue);
        this.#render();
      } catch (e) {
        console.error("Invalid JSON in data-json attribute:", e);
      }
    }
  }

  #render() {
    if (!this.isConnected) return;

    this.innerHTML = "";

    if (!this.#document) return;

    const main = render(this.#document, { asElement: true });
    this.appendChild(main);
    this.#rendered = true;
  }
}

// ============================================================================
// <mf2-feed> - Virtual list for large mf2 feeds
// ============================================================================

export interface FeedOptions {
  /** Number of items to render at once */
  batchSize?: number;
  /** Callback when more items are needed */
  onLoadMore?: () => Promise<Mf2Item[]>;
}

/**
 * Custom element for rendering large mf2 feeds with virtual scrolling support.
 * Optimized for use with sql-wasm.js pagination.
 *
 * Usage:
 * ```javascript
 * const feed = document.querySelector('mf2-feed');
 * feed.configure({ batchSize: 20, onLoadMore: () => fetchMore() });
 * feed.items = initialItems;
 * ```
 */
export class Mf2FeedElement extends HTMLElement {
  #items: Mf2Item[] = [];
  #relUrls: Record<string, RelUrl> | undefined;
  #options: FeedOptions = { batchSize: 20 };
  #observer: IntersectionObserver | null = null;
  #loading = false;
  #container: HTMLElement | null = null;
  #sentinel: HTMLElement | null = null;

  constructor() {
    super();
  }

  get items(): Mf2Item[] {
    return this.#items;
  }

  set items(value: Mf2Item[]) {
    this.#items = value;
    this.#renderAll();
  }

  get relUrls(): Record<string, RelUrl> | undefined {
    return this.#relUrls;
  }

  set relUrls(value: Record<string, RelUrl> | undefined) {
    this.#relUrls = value;
  }

  configure(options: FeedOptions) {
    this.#options = { ...this.#options, ...options };
    this.#setupObserver();
  }

  /** Append more items without re-rendering existing ones */
  appendItems(items: Mf2Item[]) {
    const fragment = document.createDocumentFragment();
    for (const item of items) {
      fragment.appendChild(renderItemElement(item, this.#relUrls));
    }
    this.#items.push(...items);
    this.#container?.insertBefore(fragment, this.#sentinel);
  }

  connectedCallback() {
    this.#container = document.createElement("section");
    this.#container.setAttribute("role", "feed");
    this.appendChild(this.#container);

    // Sentinel element for infinite scroll
    this.#sentinel = document.createElement("div");
    this.#sentinel.className = "mf2-feed-sentinel";
    this.#sentinel.setAttribute("aria-hidden", "true");
    this.#container.appendChild(this.#sentinel);

    this.#setupObserver();
    this.#renderAll();
  }

  disconnectedCallback() {
    this.#observer?.disconnect();
    this.#observer = null;
  }

  #setupObserver() {
    if (!this.#sentinel || !this.#options.onLoadMore) return;

    this.#observer?.disconnect();

    this.#observer = new IntersectionObserver(
      async (entries) => {
        const entry = entries[0];
        if (entry?.isIntersecting && !this.#loading && this.#options.onLoadMore) {
          this.#loading = true;
          try {
            const newItems = await this.#options.onLoadMore();
            if (newItems.length > 0) {
              this.appendItems(newItems);
            }
          } finally {
            this.#loading = false;
          }
        }
      },
      { rootMargin: "100px" }
    );

    this.#observer.observe(this.#sentinel);
  }

  #renderAll() {
    if (!this.#container || !this.isConnected) return;

    // Clear existing items (keep sentinel)
    while (this.#container.firstChild !== this.#sentinel) {
      this.#container.firstChild?.remove();
    }

    // Batch render using DocumentFragment for efficiency
    const fragment = document.createDocumentFragment();
    for (const item of this.#items) {
      fragment.appendChild(renderItemElement(item, this.#relUrls));
    }
    this.#container.insertBefore(fragment, this.#sentinel);
  }
}

// ============================================================================
// Registration
// ============================================================================

/**
 * Register all mf2 custom elements.
 * Call this once at application startup.
 */
export function registerElements() {
  if (!customElements.get("mf2-item")) {
    customElements.define("mf2-item", Mf2ItemElement);
  }
  if (!customElements.get("mf2-document")) {
    customElements.define("mf2-document", Mf2DocumentElement);
  }
  if (!customElements.get("mf2-feed")) {
    customElements.define("mf2-feed", Mf2FeedElement);
  }
}

// Auto-register if in browser
if (typeof window !== "undefined" && typeof customElements !== "undefined") {
  registerElements();
}
