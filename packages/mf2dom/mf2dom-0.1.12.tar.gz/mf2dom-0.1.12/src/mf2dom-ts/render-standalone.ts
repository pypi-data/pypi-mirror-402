#!/usr/bin/env npx ts-node
/**
 * Standalone CLI renderer for mf2 JSON → HTML.
 * Self-contained - no imports needed. Used by Python test suite.
 *
 * Usage: echo '{"items":[...],"rels":{},"rel-urls":{}}' | npx ts-node render-standalone.ts
 */

import { JSDOM } from "jsdom";
import { readFileSync } from "fs";

// ============================================================================
// Types (inline)
// ============================================================================

interface UrlObject {
  value: string;
  alt?: string;
  srcset?: Record<string, string>;
}

interface EValue {
  value: string;
  html: string;
  lang?: string;
}

interface RelUrl {
  rels: string[];
  text?: string;
}

type PropertyValue = string | UrlObject | EValue | Mf2Item;

interface Mf2Item {
  type: string[];
  properties: Record<string, PropertyValue[]>;
  id?: string;
  children?: Mf2Item[];
  value?: PropertyValue;
  html?: string;
}

interface Mf2Document {
  items: Mf2Item[];
  rels: Record<string, string[]>;
  "rel-urls": Record<string, RelUrl>;
}

// ============================================================================
// Setup jsdom
// ============================================================================

const dom = new JSDOM("<!DOCTYPE html><html><body></body></html>");
const doc = dom.window.document;

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
  "p-name": "strong",
  "p-summary": "p",
  "p-note": "p",
  "p-content": "p",
  "p-description": "p",
};

const URL_PROPS = new Set([
  "url", "uid", "photo", "logo", "video", "audio",
  "syndication", "in-reply-to", "like-of", "repost-of", "bookmark-of",
]);
const EMAIL_PROPS = new Set(["email"]);
const TEL_PROPS = new Set(["tel"]);
const DT_PROPS = new Set([
  "published", "updated", "start", "end", "duration", "bday", "anniversary", "rev",
]);

const PROP_ORDER = [
  "photo", "logo", "featured", "name", "nickname", "ipa",
  "author", "summary", "note", "content", "description",
  "published", "updated", "start", "end", "duration",
  "location", "url", "uid", "syndication",
  "email", "tel", "adr", "geo",
  "org", "job-title", "role", "category",
];

// ============================================================================
// DOM Helpers
// ============================================================================

function h(
  tag: string,
  attrs?: Record<string, string | undefined>,
  children?: (Node | string)[]
): HTMLElement {
  const el = doc.createElement(tag);
  if (attrs) {
    for (const [k, v] of Object.entries(attrs)) {
      if (v != null) el.setAttribute(k, v);
    }
  }
  if (children) {
    for (const child of children) {
      if (typeof child === "string") {
        el.appendChild(doc.createTextNode(child));
      } else {
        el.appendChild(child);
      }
    }
  }
  return el;
}

function text(content: string): Text {
  return doc.createTextNode(content);
}

function parseHtml(html: string): DocumentFragment {
  const tpl = doc.createElement("template");
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
  return typeof v === "object" && v !== null && "html" in v && "value" in v;
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

function renderPhoto(url: string, cls: string): HTMLElement {
  // Don't include alt="" - it changes the parsed output from string to {value, alt}
  return h("img", { class: cls, src: url });
}

function renderVideo(url: string, cls: string): HTMLElement {
  return h("video", { class: cls, src: url, controls: "" });
}

function renderAudio(url: string, cls: string): HTMLElement {
  return h("audio", { class: cls, src: url, controls: "" });
}

function renderLink(url: string, cls: string, displayText?: string, rel?: string): HTMLElement {
  return h("a", { class: cls, href: url, rel }, [displayText ?? url]);
}

function renderEmail(value: string, cls: string): HTMLElement {
  const href = value.startsWith("mailto:") ? value : `mailto:${value}`;
  const display = value.replace(/^mailto:/, "");
  return h("a", { class: cls, href }, [display]);
}

function renderTel(value: string, cls: string): HTMLElement {
  const href = value.startsWith("tel:") ? value : `tel:${value}`;
  return h("a", { class: cls, href }, [value]);
}

function renderTime(value: string, cls: string): HTMLElement {
  return h("time", { class: cls, datetime: value }, [value]);
}

function renderText(prop: string, value: string, cls: string): HTMLElement {
  const tag = SEMANTIC_PROPS[`p-${prop}`] ?? "span";
  return h(tag, { class: cls }, [value]);
}

function renderUrlObject(prop: string, obj: UrlObject): HTMLElement {
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

function renderEProperty(prop: string, value: EValue): HTMLElement {
  const div = h("div", { class: `e-${prop}` });
  if (value.html) {
    div.appendChild(parseHtml(value.html));
  } else {
    div.appendChild(text(value.value));
  }
  return div;
}

function renderRuby(name: string, ipa: string): HTMLElement {
  const ruby = h("ruby", { "aria-hidden": "true" });
  ruby.appendChild(h("strong", { class: "p-name" }, [name]));
  ruby.appendChild(h("rp", undefined, ["("]));
  const rt = doc.createElement("rt");
  rt.appendChild(text("/ "));
  rt.appendChild(h("span", { class: "p-ipa" }, [ipa]));
  rt.appendChild(text(" /"));
  ruby.appendChild(rt);
  ruby.appendChild(h("rp", undefined, [")"]));
  return ruby;
}

function renderStringProp(
  props: string[],
  value: string,
  relUrls?: Record<string, RelUrl>
): HTMLElement {
  const prop = props[0];

  if (prop === "photo" || prop === "logo") {
    return renderPhoto(value, classes(...props.map(p => `u-${p}`))!);
  }
  if (prop === "video") {
    return renderVideo(value, classes(...props.map(p => `u-${p}`))!);
  }
  if (prop === "audio") {
    return renderAudio(value, classes(...props.map(p => `u-${p}`))!);
  }
  if (URL_PROPS.has(prop) && isUrl(value)) {
    return renderLink(value, classes(...props.map(p => `u-${p}`))!, value, getRels(value, relUrls));
  }
  if (EMAIL_PROPS.has(prop)) {
    return renderEmail(value, classes(...props.map(p => `u-${p}`))!);
  }
  if (TEL_PROPS.has(prop)) {
    return renderTel(value, classes(...props.map(p => `p-${p}`))!);
  }
  if (DT_PROPS.has(prop)) {
    return renderTime(value, classes(...props.map(p => `dt-${p}`))!);
  }
  return renderText(prop, value, classes(...props.map(p => `p-${p}`))!);
}

// ============================================================================
// Item Renderer
// ============================================================================

interface ItemOptions {
  extraClasses?: string[];
  asProperty?: boolean;
  propertyPrefix?: string;
  relUrls?: Record<string, RelUrl>;
}

function embeddedPrefix(item: Mf2Item): string {
  if (typeof item.html === "string") return "e";
  if (typeof item.value === "object" && item.value !== null) return "u";
  return "p";
}

function renderItem(item: Mf2Item, opts: ItemOptions = {}): HTMLElement {
  const { extraClasses = [], asProperty = false, propertyPrefix, relUrls } = opts;
  const props = item.properties;
  const children = item.children ?? [];

  const el = h(getTag(item.type), {
    id: item.id,
    class: classes(...extraClasses, ...item.type),
  });

  if (asProperty && (propertyPrefix === "p" || propertyPrefix === "dt")) {
    if ("value" in item && typeof item.value !== "object") {
      el.appendChild(h("data", { class: "value", value: String(item.value) }));
    }
  }

  if (asProperty && propertyPrefix === "e" && typeof item.html === "string") {
    el.appendChild(parseHtml(item.html));
    return el;
  }

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

  const rendered = new Set<string>();

  for (const prop of sortProps(props)) {
    if (prop === "name" && ruby) {
      el.appendChild(renderRuby(...ruby));
      ruby = null;
    }

    if (consumed.has(prop)) continue;

    for (const v of props[prop]) {
      if (isMf2Item(v)) {
        const prefix = embeddedPrefix(v);
        el.appendChild(renderItem(v, {
          extraClasses: [`${prefix}-${prop}`],
          asProperty: true,
          propertyPrefix: prefix,
          relUrls,
        }));
        continue;
      }

      if (isEValue(v)) {
        el.appendChild(renderEProperty(prop, v));
        continue;
      }

      if (isUrlObject(v)) {
        el.appendChild(renderUrlObject(prop, v));
        continue;
      }

      if (typeof v === "string") {
        const cat = URL_PROPS.has(prop) && isUrl(v) ? "url"
          : EMAIL_PROPS.has(prop) ? "email"
          : TEL_PROPS.has(prop) ? "tel"
          : DT_PROPS.has(prop) ? "datetime"
          : `text:${prop}`;

        const key = `${v}\0${cat}`;
        if (rendered.has(key)) continue;
        rendered.add(key);

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

        el.appendChild(renderStringProp(group, v, relUrls));
        continue;
      }

      el.appendChild(renderStringProp([prop], String(v), relUrls));
    }
  }

  for (const child of children) {
    el.appendChild(renderItem(child, { relUrls }));
  }

  return el;
}

// ============================================================================
// Main Render Function
// ============================================================================

function render(mf2doc: Mf2Document): string {
  const relUrls = mf2doc["rel-urls"];
  const main = h("main");

  for (const item of mf2doc.items) {
    main.appendChild(renderItem(item, { relUrls }));
  }

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

  return main.outerHTML;
}

// ============================================================================
// CLI Entry Point
// ============================================================================

const input = readFileSync(0, "utf-8");
const mf2doc: Mf2Document = JSON.parse(input);
process.stdout.write(render(mf2doc));
