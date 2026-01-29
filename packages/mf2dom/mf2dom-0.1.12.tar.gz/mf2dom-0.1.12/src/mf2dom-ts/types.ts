/**
 * TypeScript types for mf2json (Microformats2 JSON)
 * Based on https://microformats.org/wiki/microformats2-json
 */

/** URL object with optional alt text and srcset */
export interface UrlObject {
  value: string;
  alt?: string;
  srcset?: Record<string, string>;
}

/** Embedded HTML content (e-* properties) */
export interface EValue {
  value?: string;
  html: string;
  lang?: string;
}

/** Rel URL information */
export interface RelUrl {
  rels: string[];
  text?: string;
  media?: string;
  hreflang?: string;
  type?: string;
  title?: string;
}

/** Property value types */
export type PropertyValue = string | UrlObject | EValue | Mf2Item;

/** Microformat item */
export interface Mf2Item {
  type: string[];
  properties: Record<string, PropertyValue[]>;
  id?: string;
  children?: Mf2Item[];
  value?: PropertyValue;
  html?: string;
  lang?: string;
}

/** Top-level mf2 document */
export interface Mf2Document {
  items: Mf2Item[];
  rels: Record<string, string[]>;
  "rel-urls": Record<string, RelUrl>;
}
