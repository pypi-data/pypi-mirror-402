/**
 * Microformats2 Renderer - Pure Programmatic DOM Building
 *
 * Renders mf2 JSON to semantic HTML by building the DOM tree programmatically.
 * Uses DocumentFragment for efficient batch updates with minimal reflows.
 */

import type {
  Mf2Document,
  Mf2Item,
  PropertyValue,
  EValue,
  UrlObject,
  RelUrl,
} from "./types.js";

// ============================================================================
// Configuration
// ============================================================================

const SEMANTIC_ROOTS: Record<string, string> = {
  "h-entry": "article",
  "h-feed": "section",
  "h-event": "article",
  "h-product": "article",
  "h-recipe": "article",
  "h-review": "article",
  "h-resume": "article",
  "h-adr": "address",
  "h-cite": "blockquote",
  "h-geo": "data",
};

const SEMANTIC_PROPS: Record<string, string> = {
  // Address components use address element
  "p-adr": "address",
  "p-street-address": "span",
  "p-extended-address": "span",
  "p-locality": "span",
  "p-region": "span",
  "p-postal-code": "span",
  "p-country-name": "span",
  // Name properties use strong for emphasis
  "p-name": "strong",
  // Paragraph-like properties
  "p-summary": "p",
  "p-note": "p",
  "p-content": "p",
  "p-description": "p",
  // Preformatted text (preserve line breaks)
  "p-lyrics": "pre",
  // Author info
  "p-author": "span",
};

const URL_PROPS = new Set([
  "url", "uid", "photo", "logo", "video", "audio",
  "syndication", "in-reply-to", "like-of", "repost-of", "bookmark-of",
  "follow-of", "read-of", "tag-of", "location",
]);
const EMAIL_PROPS = new Set(["email"]);
const TEL_PROPS = new Set(["tel"]);
const DT_PROPS = new Set([
  "published", "updated", "start", "end", "duration", "bday", "anniversary", "rev",
]);

// Semantic property ordering based on microformats.org wiki
// Properties are grouped by semantic meaning for good display across types:
// 1. Visual identity (photo, logo)
// 2. Name/identity
// 3. Author (for h-entry)
// 4. Description/content
// 5. Dates (important for h-entry, h-event)
// 6. Location (for h-event, h-card)
// 7. URLs and links
// 8. Contact info (email, tel)
// 9. Address details
// 10. Organization/role
// 11. Categories and other metadata
const PROP_ORDER = [
  // Visual/media first
  "photo",
  "logo",
  "featured",
  "video",
  "audio",
  // Name properties
  "name",
  "honorific-prefix",
  "given-name",
  "additional-name",
  "family-name",
  "sort-string",
  "honorific-suffix",
  "nickname",
  "ipa",
  // Author (important for h-entry)
  "author",
  // Description/content
  "summary",
  "note",
  "content",
  "lyrics",
  "description",
  // Dates (prominent for h-entry, h-event)
  "published",
  "updated",
  "start",
  "end",
  "duration",
  "bday",
  "anniversary",
  "rev",
  // Location (for h-event)
  "location",
  // URLs and links
  "url",
  "uid",
  "syndication",
  "in-reply-to",
  "like-of",
  "repost-of",
  "bookmark-of",
  "follow-of",
  "read-of",
  "read-status",
  // Contact info
  "email",
  "tel",
  "impp",
  // Address details
  "adr",
  "geo",
  "latitude",
  "longitude",
  "altitude",
  "street-address",
  "extended-address",
  "locality",
  "region",
  "postal-code",
  "country-name",
  "label",
  // Organization/role
  "org",
  "job-title",
  "role",
  // Categories and metadata
  "category",
  "rsvp",
  "attendee",
  "key",
  "sex",
  "gender-identity",
];

// ============================================================================
// DOM Builder Helpers
// ============================================================================

/** Create an element with attributes */
function h<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  attrs?: Record<string, string | undefined>,
  children?: (Node | string)[]
): HTMLElementTagNameMap[K];
function h(
  tag: string,
  attrs?: Record<string, string | undefined>,
  children?: (Node | string)[]
): HTMLElement;
function h(
  tag: string,
  attrs?: Record<string, string | undefined>,
  children?: (Node | string)[]
): HTMLElement {
  const el = document.createElement(tag);

  if (attrs) {
    for (const [k, v] of Object.entries(attrs)) {
      if (v != null) el.setAttribute(k, v);
    }
  }

  if (children) {
    for (const child of children) {
      el.append(child);
    }
  }

  return el;
}

/** Create a text node */
function text(content: string): Text {
  return document.createTextNode(content);
}

/** Parse HTML string to DocumentFragment (only for e-* content) */
function parseHtml(html: string): DocumentFragment {
  const tpl = document.createElement("template");
  tpl.innerHTML = html;
  return tpl.content;
}

// ============================================================================
// Type Guards
// ============================================================================

function isMf2Item(v: unknown): v is Mf2Item {
  return typeof v === "object" && v !== null && "type" in v && "properties" in v;
}

function isEValue(v: unknown): v is EValue {
  return typeof v === "object" && v !== null && "html" in v;
}

function isUrlObject(v: unknown): v is UrlObject {
  return typeof v === "object" && v !== null && "value" in v && ("alt" in v || "srcset" in v);
}

function isUrl(s: string): boolean {
  return s.startsWith("http://") || s.startsWith("https://") || s.startsWith("/");
}

// ============================================================================
// Helpers
// ============================================================================

function propOrder(p: string): number {
  const i = PROP_ORDER.indexOf(p);
  return i >= 0 ? i : PROP_ORDER.length;
}

function sortProps(props: Record<string, PropertyValue[]>): string[] {
  return Object.keys(props).sort((a, b) => propOrder(a) - propOrder(b));
}

function classes(...parts: (string | undefined)[]): string | undefined {
  const cls = parts.filter(Boolean).join(" ");
  return cls || undefined;
}

function getRels(url: string, relUrls?: Record<string, RelUrl>): string | undefined {
  const rels = relUrls?.[url]?.rels;
  return rels?.length ? rels.join(" ") : undefined;
}

function getTag(types: string[]): string {
  for (const t of types) {
    if (t in SEMANTIC_ROOTS) return SEMANTIC_ROOTS[t];
  }
  return "div";
}

// ============================================================================
// Property Renderers
// ============================================================================

function renderPhoto(prop: string, url: string, cls: string): HTMLImageElement {
  // Don't include alt="" - it changes the parsed output from string to {value, alt}
  return h("img", { class: cls, src: url });
}

function renderVideo(prop: string, url: string, cls: string): HTMLVideoElement {
  return h("video", { class: cls, src: url, controls: "" });
}

function renderAudio(prop: string, url: string, cls: string): HTMLAudioElement {
  return h("audio", { class: cls, src: url, controls: "" });
}

function renderLink(
  url: string,
  cls: string,
  displayText?: string,
  rel?: string
): HTMLAnchorElement {
  return h("a", { class: cls, href: url, rel }, [displayText ?? url]);
}

function renderEmail(value: string, cls: string): HTMLAnchorElement {
  const href = value.startsWith("mailto:") ? value : `mailto:${value}`;
  const display = value.replace(/^mailto:/, "");
  return h("a", { class: cls, href }, [display]);
}

function renderTel(value: string, cls: string): HTMLAnchorElement {
  const href = value.startsWith("tel:") ? value : `tel:${value}`;
  return h("a", { class: cls, href }, [value]);
}

function renderTime(value: string, cls: string): HTMLTimeElement {
  return h("time", { class: cls, datetime: value }, [value]);
}

function renderText(prop: string, value: string, cls: string): HTMLElement {
  const tag = SEMANTIC_PROPS[`p-${prop}`] ?? "span";
  return h(tag, { class: cls }, [value]);
}

function renderUrlObject(prop: string, obj: UrlObject): HTMLImageElement {
  const attrs: Record<string, string | undefined> = {
    class: `u-${prop}`,
    src: obj.value,
    alt: obj.alt,
  };

  if (obj.srcset && Object.keys(obj.srcset).length) {
    attrs.srcset = Object.entries(obj.srcset)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([k, v]) => `${v} ${k}`)
      .join(", ");
  }

  return h("img", attrs);
}

function renderEProperty(prop: string, value: EValue): HTMLDivElement {
  const div = h("div", { class: `e-${prop}` });
  if (value.html) {
    div.appendChild(parseHtml(value.html));
  } else if (value.value) {
    div.textContent = value.value;
  }
  return div;
}

function renderRuby(name: string, ipa: string): HTMLElement {
  const ruby = h("ruby", { "aria-hidden": "true" });

  ruby.appendChild(h("strong", { class: "p-name" }, [name]));
  ruby.appendChild(h("rp", undefined, ["("]));

  const rt = h("rt");
  rt.append(text("/ "), h("span", { class: "p-ipa" }, [ipa]), text(" /"));
  ruby.appendChild(rt);

  ruby.appendChild(h("rp", undefined, [")"]));

  return ruby;
}

/** Render a string property value */
function renderStringProp(
  props: string[],
  value: string,
  relUrls?: Record<string, RelUrl>,
  headingLevel?: number
): HTMLElement {
  const prop = props[0];

  // Media elements
  if (prop === "photo" || prop === "logo") {
    return renderPhoto(prop, value, classes(...props.map(p => `u-${p}`))!);
  }
  if (prop === "video") {
    return renderVideo(prop, value, classes(...props.map(p => `u-${p}`))!);
  }
  if (prop === "audio") {
    return renderAudio(prop, value, classes(...props.map(p => `u-${p}`))!);
  }

  // URL properties
  if (URL_PROPS.has(prop) && isUrl(value)) {
    return renderLink(
      value,
      classes(...props.map(p => `u-${p}`))!,
      value,
      getRels(value, relUrls)
    );
  }

  // Email
  if (EMAIL_PROPS.has(prop)) {
    return renderEmail(value, classes(...props.map(p => `u-${p}`))!);
  }

  // Telephone
  if (TEL_PROPS.has(prop)) {
    return renderTel(value, classes(...props.map(p => `p-${p}`))!);
  }

  // Datetime
  if (DT_PROPS.has(prop)) {
    return renderTime(value, classes(...props.map(p => `dt-${p}`))!);
  }

  // Default text - use heading tag for name property if headingLevel is set
  const cls = classes(...props.map(p => `p-${p}`))!;
  if (prop === "name" && headingLevel != null) {
    return h(`h${headingLevel}` as keyof HTMLElementTagNameMap, { class: cls }, [value]);
  }
  return renderText(prop, value, cls);
}

// ============================================================================
// Item Renderer
// ============================================================================

interface ItemOptions {
  extraClasses?: string[];
  asProperty?: boolean;
  propertyPrefix?: string;
  relUrls?: Record<string, RelUrl>;
  headingLevel?: number;
}

function embeddedPrefix(item: Mf2Item): string {
  if (typeof item.html === "string") return "e";
  if (typeof item.value === "object" && item.value !== null) return "u";
  return "p";
}

function renderItem(item: Mf2Item, opts: ItemOptions = {}): HTMLElement {
  const { extraClasses = [], asProperty = false, propertyPrefix, relUrls, headingLevel } = opts;
  const props = item.properties;
  const children = item.children ?? [];

  // Create root element
  const el = h(getTag(item.type), {
    id: item.id,
    class: classes(...extraClasses, ...item.type),
  });

  // VCP data node for p/dt embedded items
  if (asProperty && (propertyPrefix === "p" || propertyPrefix === "dt")) {
    if ("value" in item && typeof item.value !== "object") {
      el.appendChild(h("data", { class: "value", value: String(item.value) }));
    }
  }

  // e-* property with HTML
  if (asProperty && propertyPrefix === "e" && typeof item.html === "string") {
    el.appendChild(parseHtml(item.html));
    return el;
  }

  // Get embedded value for special name handling
  const embeddedValue = asProperty ? item.value : undefined;

  // Check for name+ipa ruby rendering
  const consumed = new Set<string>();
  let ruby: [string, string] | null = null;

  const names = props.name ?? [];
  const ipas = props.ipa ?? [];
  if (names.length && ipas.length) {
    const name = typeof names[0] === "string" ? names[0] : null;
    const ipa = typeof ipas[0] === "string" ? ipas[0] : null;
    if (name && ipa) {
      ruby = [name, ipa];
      consumed.add("name");
      consumed.add("ipa");
    }
  }

  // Check if name should be rendered as a link (single name + single URL, no ruby)
  // Don't apply when rendering as a property (changes value extraction on re-parse)
  // (name, url, list of url properties to include in class)
  let linkedName: [string, string, string[]] | null = null;
  if (!ruby && !asProperty) {
    const urls = props.url ?? [];
    if (names.length === 1 && urls.length === 1) {
      const nameVal = typeof names[0] === "string" ? names[0] : null;
      const urlVal = typeof urls[0] === "string" ? urls[0] : null;
      if (nameVal && urlVal && isUrl(urlVal)) {
        // Collect URL properties that share this URL value (like uid)
        const urlProps = ["url"];
        const uids = props.uid ?? [];
        if (uids.length === 1 && uids[0] === urlVal) {
          urlProps.push("uid");
          consumed.add("uid");
        }
        consumed.add("name");
        consumed.add("url");
        linkedName = [nameVal, urlVal, urlProps];
      }
    }
  }

  // Track rendered (value, category) pairs for grouping
  const rendered = new Set<string>();

  for (const prop of sortProps(props)) {
    // Insert ruby at name position
    if (prop === "name" && ruby) {
      const rubyEl = renderRuby(...ruby);
      if (headingLevel != null) {
        const heading = h(`h${headingLevel}` as keyof HTMLElementTagNameMap);
        heading.appendChild(rubyEl);
        el.appendChild(heading);
      } else {
        el.appendChild(rubyEl);
      }
      ruby = null;
    }

    // Render linked name at the position where "name" would appear
    if (prop === "name" && linkedName) {
      const [nameVal, urlVal, urlProps] = linkedName;
      const cls = classes("p-name", ...urlProps.map(p => `u-${p}`));
      const rel = getRels(urlVal, relUrls);
      const linkEl = h("a", { class: cls, href: urlVal, rel }, [nameVal]);
      if (headingLevel != null) {
        const heading = h(`h${headingLevel}` as keyof HTMLElementTagNameMap);
        heading.appendChild(linkEl);
        el.appendChild(heading);
      } else {
        el.appendChild(linkEl);
      }
      linkedName = null;
    }

    if (consumed.has(prop)) continue;

    // Calculate next heading level for embedded items (increment, cap at 6)
    const childHeading = headingLevel != null ? Math.min(headingLevel + 1, 6) : undefined;

    for (const v of props[prop]) {
      // Embedded mf2 item
      if (isMf2Item(v)) {
        const prefix = embeddedPrefix(v);
        el.appendChild(renderItem(v, {
          extraClasses: [`${prefix}-${prop}`],
          asProperty: true,
          propertyPrefix: prefix,
          relUrls,
          headingLevel: childHeading,
        }));
        continue;
      }

      // e-* HTML content
      if (isEValue(v)) {
        el.appendChild(renderEProperty(prop, v));
        continue;
      }

      // URL object (img with alt/srcset)
      if (isUrlObject(v)) {
        el.appendChild(renderUrlObject(prop, v));
        continue;
      }

      // If this item is itself embedded as a property, prefer dt-* for `name`
      // when its representative value differs from its `properties.name[0]`.
      if (
        asProperty &&
        propertyPrefix === "p" &&
        prop === "name" &&
        typeof embeddedValue === "string" &&
        typeof v === "string" &&
        v !== embeddedValue &&
        !v.startsWith("http://") &&
        !v.startsWith("https://")
      ) {
        // Render as time element with dt-name class (no datetime attribute)
        el.appendChild(h("time", { class: "dt-name" }, [v]));
        continue;
      }

      // String value - group by value for merged classes
      if (typeof v === "string") {
        const cat = URL_PROPS.has(prop) && isUrl(v) ? "url"
          : EMAIL_PROPS.has(prop) ? "email"
          : TEL_PROPS.has(prop) ? "tel"
          : DT_PROPS.has(prop) ? "datetime"
          : `text:${prop}`;

        const key = `${v}\0${cat}`;
        if (rendered.has(key)) continue;
        rendered.add(key);

        // Collect all props with same value+category
        const group: string[] = [];
        for (const p of sortProps(props)) {
          if (consumed.has(p)) continue;
          for (const pv of props[p]) {
            if (typeof pv !== "string" || pv !== v) continue;
            const pCat = URL_PROPS.has(p) && isUrl(pv) ? "url"
              : EMAIL_PROPS.has(p) ? "email"
              : TEL_PROPS.has(p) ? "tel"
              : DT_PROPS.has(p) ? "datetime"
              : `text:${p}`;
            if (pCat === cat && !group.includes(p)) {
              group.push(p);
            }
          }
        }

        el.appendChild(renderStringProp(group, v, relUrls, headingLevel));
        continue;
      }

      // Fallback
      el.appendChild(renderStringProp([prop], String(v), relUrls, headingLevel));
    }
  }

  // Render children - calculate next heading level (increment, cap at 6)
  const childrenHeading = headingLevel != null ? Math.min(headingLevel + 1, 6) : undefined;
  for (const child of children) {
    el.appendChild(renderItem(child, { relUrls, headingLevel: childrenHeading }));
  }

  return el;
}

// ============================================================================
// Public API
// ============================================================================

export interface RenderOptions {
  /** Return HTMLElement instead of string */
  asElement?: boolean;
  /** If set, render name properties as heading elements starting at this level (1-6).
   *  Names in nested items use incrementing levels (capped at h6).
   *  Default is undefined (render as <strong>). */
  topHeading?: number;
}

/**
 * Render an mf2 document to HTML.
 */
export function render(doc: Mf2Document, opts?: { asElement: true; topHeading?: number }): HTMLElement;
export function render(doc: Mf2Document, opts?: { asElement?: false; topHeading?: number }): string;
export function render(doc: Mf2Document, opts: RenderOptions = {}): string | HTMLElement {
  const relUrls = doc["rel-urls"];
  const { topHeading } = opts;
  const main = h("main");

  // Render items
  for (const item of doc.items) {
    main.appendChild(renderItem(item, { relUrls, headingLevel: topHeading }));
  }

  // Render rel-urls as nav
  if (relUrls && Object.keys(relUrls).length) {
    const nav = h("nav");
    for (const url of Object.keys(relUrls).sort()) {
      const info = relUrls[url];
      nav.appendChild(h("a", {
        href: url,
        rel: info.rels?.length ? info.rels.join(" ") : undefined,
      }, [info.text ?? url]));
    }
    main.appendChild(nav);
  }

  return opts.asElement ? main : main.outerHTML;
}

export interface RenderItemElementOptions {
  relUrls?: Record<string, RelUrl>;
  topHeading?: number;
}

/**
 * Render a single mf2 item to an HTMLElement.
 */
export function renderItemElement(
  item: Mf2Item,
  options: RenderItemElementOptions = {}
): HTMLElement {
  const { relUrls, topHeading } = options;
  return renderItem(item, { relUrls, headingLevel: topHeading });
}

export interface RenderItemsOptions {
  relUrls?: Record<string, RelUrl>;
  topHeading?: number;
}

/**
 * Render multiple items efficiently using DocumentFragment.
 */
export function renderItems(
  items: Mf2Item[],
  options: RenderItemsOptions = {}
): DocumentFragment {
  const { relUrls, topHeading } = options;
  const fragment = document.createDocumentFragment();
  for (const item of items) {
    fragment.appendChild(renderItem(item, { relUrls, headingLevel: topHeading }));
  }
  return fragment;
}

export { parseHtml as parseHtmlFragment };
