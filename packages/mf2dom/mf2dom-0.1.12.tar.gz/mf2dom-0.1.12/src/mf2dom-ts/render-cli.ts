#!/usr/bin/env node
/**
 * CLI tool to render mf2 JSON to HTML.
 * Used by Python test suite for cross-validation.
 *
 * Usage: echo '{"items":[],"rels":{},"rel-urls":{}}' | npx ts-node render-cli.ts
 */

import { JSDOM } from "jsdom";
import { readFileSync } from "fs";

// Setup global DOM APIs using jsdom
const dom = new JSDOM("<!DOCTYPE html><html><body></body></html>");
globalThis.document = dom.window.document;
globalThis.DocumentFragment = dom.window.DocumentFragment;
globalThis.HTMLElement = dom.window.HTMLElement;
globalThis.Text = dom.window.Text;

// Now import the renderer (it uses global document)
import { render } from "./renderer.js";
import type { Mf2Document } from "./types.js";

// Read JSON from stdin
const input = readFileSync(0, "utf-8");
const doc: Mf2Document = JSON.parse(input);

// Render and output HTML
const html = render(doc);
process.stdout.write(html);
