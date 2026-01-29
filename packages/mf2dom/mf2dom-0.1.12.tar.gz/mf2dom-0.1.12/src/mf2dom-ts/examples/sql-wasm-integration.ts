/**
 * Example: mf2dom-ts with sql-wasm.js integration
 *
 * Shows how to store mf2 entries in SQLite and render them efficiently.
 */

import type { Mf2Item, Mf2Document } from "../types.js";
import { render, renderItemElement } from "../renderer.js";
import { Mf2FeedElement, registerElements } from "../components.js";

// Type for sql-wasm.js Database
interface SqlJsDatabase {
  run(sql: string, params?: unknown[]): void;
  exec(sql: string): { columns: string[]; values: unknown[][] }[];
  prepare(sql: string): {
    bind(params?: unknown[]): unknown;
    step(): boolean;
    getAsObject(): Record<string, unknown>;
    free(): void;
  };
}

// ============================================================================
// Database Schema & Operations
// ============================================================================

const SCHEMA = `
  CREATE TABLE IF NOT EXISTS mf2_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,           -- Primary h-* type (e.g., 'h-entry')
    json TEXT NOT NULL,           -- Full mf2 JSON
    published TEXT,               -- Extracted for indexing/sorting
    url TEXT,                     -- Extracted for lookup
    created_at TEXT DEFAULT (datetime('now'))
  );

  CREATE INDEX IF NOT EXISTS idx_mf2_type ON mf2_entries(type);
  CREATE INDEX IF NOT EXISTS idx_mf2_published ON mf2_entries(published);
  CREATE INDEX IF NOT EXISTS idx_mf2_url ON mf2_entries(url);
`;

export class Mf2Store {
  constructor(private db: SqlJsDatabase) {
    this.db.run(SCHEMA);
  }

  /** Store an mf2 item */
  insert(item: Mf2Item): number {
    const type = item.type[0] ?? "h-item";
    const published = (item.properties.published?.[0] as string) ?? null;
    const url = (item.properties.url?.[0] as string) ?? null;
    const json = JSON.stringify(item);

    this.db.run(
      `INSERT INTO mf2_entries (type, json, published, url) VALUES (?, ?, ?, ?)`,
      [type, json, published, url]
    );

    // Get last insert ID
    const result = this.db.exec("SELECT last_insert_rowid()");
    return result[0]?.values[0]?.[0] as number;
  }

  /** Bulk insert for efficiency */
  insertMany(items: Mf2Item[]): void {
    this.db.run("BEGIN TRANSACTION");
    try {
      for (const item of items) {
        this.insert(item);
      }
      this.db.run("COMMIT");
    } catch (e) {
      this.db.run("ROLLBACK");
      throw e;
    }
  }

  /** Get item by ID */
  getById(id: number): Mf2Item | null {
    const stmt = this.db.prepare("SELECT json FROM mf2_entries WHERE id = ?");
    stmt.bind([id]);
    if (stmt.step()) {
      const row = stmt.getAsObject();
      stmt.free();
      return JSON.parse(row.json as string);
    }
    stmt.free();
    return null;
  }

  /** Get items by type with pagination */
  getByType(type: string, limit = 20, offset = 0): Mf2Item[] {
    const stmt = this.db.prepare(
      `SELECT json FROM mf2_entries WHERE type = ? ORDER BY published DESC LIMIT ? OFFSET ?`
    );
    stmt.bind([type, limit, offset]);

    const items: Mf2Item[] = [];
    while (stmt.step()) {
      const row = stmt.getAsObject();
      items.push(JSON.parse(row.json as string));
    }
    stmt.free();
    return items;
  }

  /** Get all entries with pagination (for feeds) */
  getRecent(limit = 20, offset = 0): Mf2Item[] {
    const stmt = this.db.prepare(
      `SELECT json FROM mf2_entries ORDER BY published DESC, id DESC LIMIT ? OFFSET ?`
    );
    stmt.bind([limit, offset]);

    const items: Mf2Item[] = [];
    while (stmt.step()) {
      const row = stmt.getAsObject();
      items.push(JSON.parse(row.json as string));
    }
    stmt.free();
    return items;
  }

  /** Count total entries */
  count(type?: string): number {
    const sql = type
      ? "SELECT COUNT(*) FROM mf2_entries WHERE type = ?"
      : "SELECT COUNT(*) FROM mf2_entries";
    const result = this.db.exec(sql);
    return (result[0]?.values[0]?.[0] as number) ?? 0;
  }
}

// ============================================================================
// Rendering Integration
// ============================================================================

/**
 * Render entries from the database to a container element.
 */
export function renderEntriesTo(
  store: Mf2Store,
  container: HTMLElement,
  options: { type?: string; limit?: number; offset?: number } = {}
): void {
  const { type, limit = 20, offset = 0 } = options;
  const items = type
    ? store.getByType(type, limit, offset)
    : store.getRecent(limit, offset);

  // Use DocumentFragment for efficient batch insert
  const fragment = document.createDocumentFragment();
  for (const item of items) {
    fragment.appendChild(renderItemElement(item));
  }
  container.appendChild(fragment);
}

/**
 * Create an infinite-scrolling feed from the database.
 */
export function createFeedFromStore(
  store: Mf2Store,
  options: { type?: string; batchSize?: number } = {}
): Mf2FeedElement {
  const { type, batchSize = 20 } = options;
  let offset = 0;

  // Ensure elements are registered
  registerElements();

  const feed = document.createElement("mf2-feed") as Mf2FeedElement;

  feed.configure({
    batchSize,
    onLoadMore: async () => {
      offset += batchSize;
      return type
        ? store.getByType(type, batchSize, offset)
        : store.getRecent(batchSize, offset);
    },
  });

  // Load initial items
  const initialItems = type
    ? store.getByType(type, batchSize, 0)
    : store.getRecent(batchSize, 0);
  feed.items = initialItems;

  return feed;
}

// ============================================================================
// Full Example Usage
// ============================================================================

/**
 * Example: Complete setup with sql-wasm.js
 *
 * ```typescript
 * import initSqlJs from 'sql.js';
 * import { Mf2Store, createFeedFromStore } from './sql-wasm-integration.js';
 *
 * async function main() {
 *   // Initialize sql.js
 *   const SQL = await initSqlJs({
 *     locateFile: file => `https://sql.js.org/dist/${file}`
 *   });
 *
 *   // Create database (or load from IndexedDB/file)
 *   const db = new SQL.Database();
 *   const store = new Mf2Store(db);
 *
 *   // Store some entries
 *   store.insertMany([
 *     {
 *       type: ['h-entry'],
 *       properties: {
 *         name: ['My First Post'],
 *         content: ['Hello, world!'],
 *         published: ['2024-01-15T10:00:00Z'],
 *         url: ['https://example.com/posts/1']
 *       }
 *     },
 *     {
 *       type: ['h-entry'],
 *       properties: {
 *         name: ['Another Post'],
 *         summary: ['This is a summary'],
 *         published: ['2024-01-16T14:30:00Z'],
 *         author: [{
 *           type: ['h-card'],
 *           properties: { name: ['Alice'] },
 *           value: 'Alice'
 *         }]
 *       }
 *     }
 *   ]);
 *
 *   // Create infinite-scrolling feed
 *   const feed = createFeedFromStore(store, { type: 'h-entry' });
 *   document.getElementById('feed-container')!.appendChild(feed);
 *
 *   // Or render directly
 *   const container = document.getElementById('entries')!;
 *   renderEntriesTo(store, container, { limit: 10 });
 * }
 *
 * main();
 * ```
 */

export { render, renderItemElement } from "../renderer.js";
